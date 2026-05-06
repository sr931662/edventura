import 'package:dio/dio.dart';
import 'package:get/get.dart' hide Response;
import 'package:pretty_dio_logger/pretty_dio_logger.dart';
import 'package:flutter/foundation.dart';
import 'api_endpoints.dart';
import '../storage/secure_storage.dart';

class ApiClient {
  ApiClient._();
  static final ApiClient instance = ApiClient._();
  late final Dio _dio;

  void init() {
    _dio = Dio(BaseOptions(
      baseUrl: ApiEndpoints.baseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 30),
      headers: {
        'Content-Type': 'application/json',
        'Accept':       'application/json',
      },
    ));

    _dio.interceptors.addAll([
      _AuthInterceptor(),
      if (kDebugMode)
        PrettyDioLogger(
          requestHeader: false,
          requestBody:   true,
          responseBody:  true,
          error:         true,
          compact:       true,
        ),
    ]);
  }

  // ── Convenience methods ────────────────────────────────────────

  Future<Response> get(
      String path, {
        Map<String, dynamic>? query,
      }) =>
      _dio.get(path, queryParameters: query);

  Future<Response> post(
      String path, {
        dynamic data,
      }) =>
      _dio.post(path, data: data);

  Future<Response> put(
      String path, {
        dynamic data,
      }) =>
      _dio.put(path, data: data);

  Future<Response> patch(
      String path, {
        dynamic data,
      }) =>
      _dio.patch(path, data: data);

  Future<Response> delete(String path) =>
      _dio.delete(path);
}

// ── Auth Interceptor ───────────────────────────────────────────────

class _AuthInterceptor extends Interceptor {
  @override
  Future<void> onRequest(
      RequestOptions options,
      RequestInterceptorHandler handler,
      ) async {
    final token = await SecureStorage.instance.getToken();
    if (token != null && token.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    if (err.response?.statusCode == 401) {
      final currentRoute = Get.currentRoute;

      // Only auto-logout + redirect if NOT already on login screen
      // Prevents circular navigation loop that was causing keyboard dismiss
      if (currentRoute != '/login' && currentRoute.isNotEmpty) {
        SecureStorage.instance.clearAll();
        Get.offAllNamed('/login');
      }
    }
    handler.next(err);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    handler.next(response);
  }
}