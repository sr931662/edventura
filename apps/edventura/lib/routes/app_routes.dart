import 'package:get/get.dart';
import '../features/authentication/screens/login.dart';
// Add imports as you build screens

abstract class AppRoutes {
  AppRoutes._();

  // Auth
  static const login         = '/login';
  static const signup        = '/signup';

  // Tier 1 — Strategic Governance
  static const ownerDash     = '/dashboard/owner';
  static const leaderDash    = '/dashboard/leader';
  static const adminDash     = '/dashboard/admin';

  // Tier 2 — Academic Operations
  static const teacherDash   = '/dashboard/teacher';
  static const hodDash       = '/dashboard/hod';

  // Tier 4 — External (build these first — thesis screenshots)
  static const studentDash   = '/dashboard/student';  // Screenshot A-2
  static const parentDash    = '/dashboard/parent';

  // Feature screens
  static const attendance    = '/attendance';
  static const fees          = '/fees';
  static const daisy         = '/daisy';           // Screenshot A-3
  static const announcements = '/announcements';
  static const profile       = '/profile';

  static final List<GetPage> pages = [
    GetPage(
      name: login,
      page: () => const LoginScreen(),
      transition: Transition.fade,
    ),
    // Uncomment as you build each screen:
    // GetPage(name: studentDash, page: () => const StudentDashboard()),
    // GetPage(name: teacherDash, page: () => const TeacherDashboard()),
    // GetPage(name: parentDash,  page: () => const ParentDashboard()),
    // GetPage(name: daisy,       page: () => const DaisyScreen()),
    // GetPage(name: attendance,  page: () => const AttendanceScreen()),
  ];

  /// Called after login — routes to correct dashboard by role string
  /// Match these strings exactly with your FastAPI /auth/login response
  static void routeByRole(String role) {
    const map = {
      'institution_owner':  ownerDash,
      'institution_leader': leaderDash,
      'institution_admin':  adminDash,
      'sub_admin':          adminDash,
      'class_teacher':      teacherDash,
      'subject_teacher':    teacherDash,
      'head_of_department': hodDash,
      'student':            studentDash,
      'parent':             parentDash,
      // Add remaining 17 roles as you build their screens
    };
    Get.offAllNamed(map[role] ?? login);
  }
}