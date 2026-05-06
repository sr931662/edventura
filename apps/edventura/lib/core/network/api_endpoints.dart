abstract class ApiEndpoints {
  ApiEndpoints._();

  // ── Base URL ───────────────────────────────────────────────────────
  // Android Emulator: 10.0.2.2 = your PC's localhost
  // iOS Simulator:    127.0.0.1
  // Real Device:      your PC's LAN IP (check via ipconfig on Windows)
  // Production:       https://api.edventura.in/api/v1
  static const baseUrl = 'http://10.0.2.2:8000/api/v1';

  // ── Auth (Ch 5.1) ──────────────────────────────────────────────────
  static const login          = '/auth/login';
  static const logout         = '/auth/logout';
  static const refresh        = '/auth/refresh';
  static const forgotPassword = '/auth/forgot-password';

  // ── Profile ────────────────────────────────────────────────────────
  static const profile        = '/user/profile';

  // ── Students (Ch 5.5) ──────────────────────────────────────────────
  static const students           = '/students';
  static String studentById(String id) => '/students/$id';

  // ── Attendance (Ch 6.1) ────────────────────────────────────────────
  static const attendance         = '/attendance';
  static const markAttendance     = '/attendance/mark';

  // ── Fees (Ch 6.2) ──────────────────────────────────────────────────
  static const feeStructure       = '/fees/structure';
  static const feePayments        = '/fees/payments';
  static const paymentInit        = '/fees/payment/init';    // Razorpay
  static const paymentVerify      = '/fees/payment/verify';

  // ── Communication (Ch 6.3) ────────────────────────────────────────
  static const announcements      = '/announcements';
  static const messages           = '/messages';
  static const notifications      = '/notifications';

  // ── Daisy AI TutorBot (Ch 7.4.3) ──────────────────────────────────
  static const daisyChat          = '/ai/tutor/chat';
  static const daisyJobStatus     = '/ai/tutor/job';  // async polling

  // ── Dashboard stats ────────────────────────────────────────────────
  static const studentDashboard   = '/dashboard/student';
  static const teacherDashboard   = '/dashboard/teacher';
  static const parentDashboard    = '/dashboard/parent';
}