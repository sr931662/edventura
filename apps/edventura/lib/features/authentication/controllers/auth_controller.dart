import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:dio/dio.dart';
import '../../../core/network/api_client.dart';
import '../../../core/network/api_endpoints.dart';
import '../../../core/storage/secure_storage.dart';

class AuthController extends GetxController {
  // ── Text controllers ───────────────────────────────────────────
  final emailController    = TextEditingController();
  final passwordController = TextEditingController();

  // ── Reactive state ─────────────────────────────────────────────
  final isLoading       = false.obs;
  final obscurePassword = true.obs;

  // ── Lifecycle ──────────────────────────────────────────────────
  @override
  void onInit() {
    super.onInit();
    _checkExistingSession();
  }

  @override
  void onClose() {
    emailController.dispose();
    passwordController.dispose();
    super.onClose();
  }

  // ── Public methods ─────────────────────────────────────────────

  void togglePasswordVisibility() =>
      obscurePassword.value = !obscurePassword.value;

  Future<void> loginUser() async {
    isLoading.value = true;
    try {
      final res = await ApiClient.instance.post(
        ApiEndpoints.login,
        data: {
          'email':    emailController.text.trim(),
          'password': passwordController.text,
        },
      );

      final data = res.data;
      String token   = '';
      String refresh = '';
      String role    = '';
      String tenant  = '';
      String uid     = '';

      // Handle both flat and nested FastAPI response structures
      if (data['access_token'] != null) {
        // Flat: { access_token, refresh_token, user: { role, ... } }
        token   = data['access_token'] as String;
        refresh = (data['refresh_token'] ?? '').toString();
        role    = (data['user']?['role'] ?? data['role'] ?? '').toString();
        tenant  = (data['user']?['tenant_id'] ?? data['tenant_id'] ?? '')
            .toString();
        uid     = (data['user']?['id'] ?? data['id'] ?? '').toString();
      } else if (data['data']?['access_token'] != null) {
        // Nested: { data: { access_token, refresh_token, user: {...} } }
        final d = data['data'];
        token   = d['access_token'] as String;
        refresh = (d['refresh_token'] ?? '').toString();
        role    = (d['user']?['role'] ?? '').toString();
        tenant  = (d['user']?['tenant_id'] ?? '').toString();
        uid     = (d['user']?['id'] ?? '').toString();
      } else {
        throw Exception('Unrecognised response. Check FastAPI /auth/login.');
      }

      await SecureStorage.instance.saveToken(token);
      await SecureStorage.instance.saveRefresh(refresh);
      await SecureStorage.instance.saveRole(role);
      await SecureStorage.instance.saveTenant(tenant);
      await SecureStorage.instance.saveUserId(uid);

      _routeByRole(role);

    } on DioException catch (e) {
      final msg = e.response?.data?['detail'] ??
          e.response?.data?['message'] ??
          _friendlyDioError(e);
      _showError(msg.toString());
    } catch (e) {
      _showError('Something went wrong. Please try again.');
    } finally {
      isLoading.value = false;
    }
  }

  Future<void> logoutUser() async {
    try {
      await ApiClient.instance.post(ApiEndpoints.logout);
    } catch (_) {}
    await SecureStorage.instance.clearAll();
    Get.offAllNamed('/login');
  }

  // ── Private ────────────────────────────────────────────────────

  Future<void> _checkExistingSession() async {
    final token = await SecureStorage.instance.getToken();
    if (token == null) return; // No token — stay on login

    try {
      final res = await ApiClient.instance.get(ApiEndpoints.profile);

      // Parse role from profile response
      final role = res.data?['data']?['role'] ??
          res.data?['role'] ??
          await SecureStorage.instance.getRole();

      if (role != null && role.toString().isNotEmpty) {
        _routeByRole(role.toString());
      }

    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        // Token expired — clear storage, stay on login
        // DO NOT navigate — we're already on /login
        await SecureStorage.instance.clearAll();
      }
      // For network errors (no internet) — silently ignore
      // User stays on login, can try manually
    } catch (_) {
      // Any other error — silently ignore, stay on login
    }
  }

  void _routeByRole(String role) {
    const roleMap = {
      // Tier 1 — Strategic Governance
      'institution_owner':  '/dashboard/owner',
      'institution_leader': '/dashboard/leader',
      'institution_admin':  '/dashboard/admin',
      'sub_admin':          '/dashboard/admin',
      'superadmin':         '/dashboard/admin',

      // Tier 2 — Academic Operations
      'class_teacher':      '/dashboard/teacher',
      'subject_teacher':    '/dashboard/teacher',
      'head_of_department': '/dashboard/hod',
      'finance_head':       '/dashboard/finance-head',
      'registrar':          '/dashboard/admin',
      'accountant':         '/dashboard/admin',
      'exam_controller':    '/dashboard/admin',
      'librarian':          '/dashboard/admin',
      'academic_coordinator': '/dashboard/admin',

      // Tier 3 — Support & Ops
      'counsellor':         '/dashboard/admin',
      'hr_manager':         '/dashboard/admin',
      'it_head':            '/dashboard/admin',
      'transport_manager':  '/dashboard/admin',
      'hostel_manager':     '/dashboard/admin',
      'medical_staff':      '/dashboard/admin',
      'activity_coordinator': '/dashboard/admin',
      'sports_coach':       '/dashboard/admin',
      'admission_counsellor': '/dashboard/admin',
      'facility_manager':   '/dashboard/admin',
      'vendor':             '/dashboard/admin',

      // Tier 4 — External Stakeholders
      'student':            '/dashboard/student',
      'parent':             '/dashboard/parent',
    };

    final route = roleMap[role.toLowerCase().trim()];

    if (route == null) {
      _showError('Unknown role: "$role". Contact your administrator.');
      return;
    }

    Get.offAllNamed(route);
  }

  String _friendlyDioError(DioException e) {
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.receiveTimeout:
        return 'Connection timed out. Check your internet.';
      case DioExceptionType.badResponse:
        final code = e.response?.statusCode;
        if (code == 401) return 'Invalid email or password.';
        if (code == 403) return 'Account suspended. Contact admin.';
        if (code == 404) return 'Server not reachable. Check base URL.';
        if (code == 422) return 'Invalid input. Check your credentials.';
        if (code != null && code >= 500) return 'Server error. Try again.';
        return 'Request failed ($code).';
      case DioExceptionType.connectionError:
        return 'No internet connection.';
      default:
        return 'Something went wrong. Try again.';
    }
  }

  void _showError(String message) {
    Get.snackbar(
      'Login Failed',
      message,
      snackPosition: SnackPosition.BOTTOM,
      backgroundColor: const Color(0xFFEF4444),
      colorText: Colors.white,
      borderRadius: 14,
      margin: const EdgeInsets.all(16),
      icon: const Icon(Icons.error_outline, color: Colors.white),
      duration: const Duration(seconds: 4),
    );
  }
}