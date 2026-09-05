import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

final secureStorageProvider = Provider<SecureStorageService>((ref) {
  return SecureStorageService();
});

class SecureStorageService {
  static const _keyToken   = 'access_token';
  static const _keyRefresh = 'refresh_token';
  static const _keyUserId  = 'user_id';
  static const _keyRole    = 'user_role';

  final _storage = const FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
    iOptions: IOSOptions(accessibility: KeychainAccessibility.first_unlock),
  );

  Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
  }) async {
    await _storage.write(key: _keyToken,   value: accessToken);
    await _storage.write(key: _keyRefresh, value: refreshToken);
  }

  Future<String?> getToken() => _storage.read(key: _keyToken);
  Future<String?> getRefreshToken() => _storage.read(key: _keyRefresh);

  Future<void> saveUserInfo({required String userId, required String role}) async {
    await _storage.write(key: _keyUserId, value: userId);
    await _storage.write(key: _keyRole,   value: role);
  }

  Future<String?> getUserId() => _storage.read(key: _keyUserId);
  Future<String?> getRole()   => _storage.read(key: _keyRole);

  Future<bool> isAuthenticated() async {
    final token = await getToken();
    return token != null && token.isNotEmpty;
  }

  Future<void> clearAll() => _storage.deleteAll();
}
