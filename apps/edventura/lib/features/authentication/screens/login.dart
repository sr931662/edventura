import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:edventura/utils/theme/theme_colors.dart';
import 'package:edventura/features/authentication/controllers/auth_controller.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  late final AuthController authController;
  final GlobalKey<FormState> formKey = GlobalKey<FormState>();
  final RxBool keepLoggedIn = false.obs;

  @override
  void initState() {
    super.initState();
    // Controller ek hi baar initialize — build() se bahar
    authController = Get.put(AuthController());
  }

  void handleLogin() {
    // Keyboard close karo before validation
    FocusScope.of(context).unfocus();

    // Viva demo mode
    if (authController.emailController.text.trim() == 'admin@demo.com' &&
        authController.passwordController.text == '123456') {
      Get.offAllNamed('/dashboard/admin');
      return;
    }

    if (formKey.currentState!.validate()) {
      authController.loginUser();
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final Size size = MediaQuery.of(context).size;

    return Scaffold(
      resizeToAvoidBottomInset: true,
      body: Stack(
        children: [
          // 1. Background gradient
          Container(
            height: size.height,
            width: size.width,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: isDark
                    ? [TColors.darkBackground, Colors.black]
                    : [const Color(0xFFD4FCFF), const Color(0xFFF3E5F5)],
              ),
            ),
          ),

          // 2. Glowing orbs — IgnorePointer so touches pass through
          IgnorePointer(
            child: Positioned(
              top: -80,
              left: -80,
              child: Container(
                width: 250,
                height: 250,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: Colors.transparent,
                  boxShadow: [
                    BoxShadow(
                      color: TColors.primary.withOpacity(0.3),
                      blurRadius: 100,
                      spreadRadius: 20,
                    ),
                  ],
                ),
              ),
            ),
          ),
          IgnorePointer(
            child: Positioned(
              bottom: -80,
              right: -80,
              child: Container(
                width: 250,
                height: 250,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: Colors.transparent,
                  boxShadow: [
                    BoxShadow(
                      color: TColors.secondary.withOpacity(0.3),
                      blurRadius: 100,
                      spreadRadius: 20,
                    ),
                  ],
                ),
              ),
            ),
          ),

          // 3. Main content
          Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 40),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  // Logo
                  Hero(
                    tag: 'app_logo',
                    child: Image.asset(
                      'assets/logos/ic_launcher.png',
                      height: 100,
                      errorBuilder: (ctx, err, st) => ShaderMask(
                        shaderCallback: (b) => const LinearGradient(
                          colors: [TColors.secondary, TColors.primary],
                        ).createShader(b),
                        child: const Icon(
                          Icons.menu_book_rounded,
                          size: 90,
                          color: Colors.white,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 40),

                  // Login card
                  Container(
                    padding: const EdgeInsets.all(30),
                    decoration: BoxDecoration(
                      color: isDark
                          ? Colors.white.withOpacity(0.05)
                          : Colors.white,
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(
                        color: isDark
                            ? Colors.white.withOpacity(0.1)
                            : Colors.white,
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: TColors.primary.withOpacity(0.1),
                          blurRadius: 40,
                          offset: const Offset(0, 15),
                        ),
                      ],
                    ),
                    child: Form(
                      key: formKey,
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            'Welcome Back',
                            style: Theme.of(context)
                                .textTheme
                                .headlineSmall
                                ?.copyWith(
                              fontWeight: FontWeight.bold,
                              color: isDark
                                  ? Colors.white
                                  : TColors.textPrimary,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'EdVentura Educational OS',
                            style: Theme.of(context)
                                .textTheme
                                .bodySmall
                                ?.copyWith(
                              color: isDark
                                  ? Colors.white54
                                  : TColors.textSecondary,
                            ),
                          ),
                          const SizedBox(height: 30),

                          // Email field
                          TextFormField(
                            controller: authController.emailController,
                            keyboardType: TextInputType.emailAddress,
                            textInputAction: TextInputAction.next,
                            style: TextStyle(
                              color: isDark
                                  ? Colors.white
                                  : TColors.textPrimary,
                            ),
                            decoration: const InputDecoration(
                              hintText: 'User ID / Email',
                              prefixIcon: Icon(Icons.person_outline),
                            ),
                            validator: (v) {
                              if (v == null || v.trim().isEmpty) {
                                return 'Email is required';
                              }
                              return null;
                            },
                          ),
                          const SizedBox(height: 20),

                          // Password field
                          Obx(() => TextFormField(
                            controller: authController.passwordController,
                            obscureText: authController.obscurePassword.value,
                            textInputAction: TextInputAction.done,
                            style: TextStyle(
                              color: isDark
                                  ? Colors.white
                                  : TColors.textPrimary,
                            ),
                            decoration: InputDecoration(
                              hintText: 'Password',
                              prefixIcon: const Icon(Icons.lock_outline),
                              suffixIcon: IconButton(
                                icon: Icon(
                                  authController.obscurePassword.value
                                      ? Icons.visibility_off_outlined
                                      : Icons.visibility_outlined,
                                ),
                                onPressed:
                                authController.togglePasswordVisibility,
                              ),
                            ),
                            validator: (v) {
                              if (v == null || v.isEmpty) {
                                return 'Password is required';
                              }
                              if (v.length < 6) {
                                return 'Minimum 6 characters';
                              }
                              return null;
                            },
                            onFieldSubmitted: (_) => handleLogin(),
                          )),
                          const SizedBox(height: 15),

                          // Keep me logged in + Forgot password
                          Row(
                            children: [
                              Obx(() => SizedBox(
                                height: 24,
                                width: 24,
                                child: Checkbox(
                                  value: keepLoggedIn.value,
                                  activeColor: TColors.primary,
                                  onChanged: (val) =>
                                  keepLoggedIn.value = val!,
                                ),
                              )),
                              const SizedBox(width: 8),
                              Text(
                                'Keep me logged in',
                                style: Theme.of(context).textTheme.bodyMedium,
                              ),
                              const Spacer(),
                              GestureDetector(
                                onTap: () => Get.snackbar(
                                  'Coming Soon',
                                  'Password reset coming soon.',
                                  snackPosition: SnackPosition.BOTTOM,
                                ),
                                child: Text(
                                  'Forgot Password?',
                                  style: Theme.of(context)
                                      .textTheme
                                      .bodySmall
                                      ?.copyWith(
                                    color: TColors.primary,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 25),

                          // Gradient login button
                          Obx(() => Container(
                            width: double.infinity,
                            height: 55,
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(14),
                              gradient: LinearGradient(
                                colors: authController.isLoading.value
                                    ? [Colors.grey, Colors.grey]
                                    : [TColors.secondary, TColors.primary],
                              ),
                              boxShadow: [
                                BoxShadow(
                                  color: TColors.primary.withOpacity(0.3),
                                  blurRadius: 15,
                                  offset: const Offset(0, 8),
                                ),
                              ],
                            ),
                            child: ElevatedButton(
                              onPressed: authController.isLoading.value
                                  ? null
                                  : handleLogin,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.transparent,
                                shadowColor: Colors.transparent,
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(14),
                                ),
                              ),
                              child: authController.isLoading.value
                                  ? const SizedBox(
                                height: 22,
                                width: 22,
                                child: CircularProgressIndicator(
                                  color: Colors.white,
                                  strokeWidth: 2.5,
                                ),
                              )
                                  : const Text(
                                'LOGIN',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 16,
                                  letterSpacing: 1.5,
                                ),
                              ),
                            ),
                          )),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 40),

                  // Higher Security
                  Text(
                    'Higher Security',
                    style: Theme.of(context).textTheme.labelMedium?.copyWith(
                      color: isDark
                          ? Colors.white54
                          : TColors.textSecondary,
                    ),
                  ),
                  const SizedBox(height: 15),
                  Row(
                    children: [
                      Expanded(
                        child: _buildSecurityButton(
                          context, Icons.face, 'Face ID',
                        ),
                      ),
                      const SizedBox(width: 15),
                      Expanded(
                        child: _buildSecurityButton(
                          context, Icons.fingerprint, 'Biometric',
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSecurityButton(
      BuildContext context, IconData icon, String label) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return GestureDetector(
      onTap: () => Get.snackbar(
        'Coming Soon',
        '$label authentication coming soon.',
        snackPosition: SnackPosition.BOTTOM,
      ),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: isDark
              ? Colors.white.withOpacity(0.05)
              : Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: TColors.primary.withOpacity(0.2)),
          boxShadow: isDark
              ? []
              : [
            BoxShadow(
              color: Colors.grey.withOpacity(0.1),
              blurRadius: 10,
              offset: const Offset(0, 5),
            ),
          ],
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: TColors.primary, size: 20),
            const SizedBox(width: 8),
            Text(
              label,
              style: const TextStyle(
                fontWeight: FontWeight.w600,
                fontSize: 13,
              ),
            ),
          ],
        ),
      ),
    );
  }
}