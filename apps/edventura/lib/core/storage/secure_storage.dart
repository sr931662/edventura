import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SecureStorage {
  SecureStorage._();
  static final SecureStorage instance = SecureStorage._();

  final _s = const FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
  );

  // Keys
  static const _kToken   = 'ev_access_token';
  static const _kRefresh = 'ev_refresh_token';
  static const _kRole    = 'ev_user_role';
  static const _kTenant  = 'ev_tenant_id';
  static const _kUserId  = 'ev_user_id';

  // Write
  Future<void> saveToken(String v)   => _s.write(key: _kToken,   value: v);
  Future<void> saveRefresh(String v) => _s.write(key: _kRefresh, value: v);
  Future<void> saveRole(String v)    => _s.write(key: _kRole,    value: v);
  Future<void> saveTenant(String v)  => _s.write(key: _kTenant,  value: v);
  Future<void> saveUserId(String v)  => _s.write(key: _kUserId,  value: v);

  // Read
  Future<String?> getToken()   => _s.read(key: _kToken);
  Future<String?> getRefresh() => _s.read(key: _kRefresh);
  Future<String?> getRole()    => _s.read(key: _kRole);
  Future<String?> getTenant()  => _s.read(key: _kTenant);
  Future<String?> getUserId()  => _s.read(key: _kUserId);

  // Clear on logout
  Future<void> clearAll() => _s.deleteAll();
}