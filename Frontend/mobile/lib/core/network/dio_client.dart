import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../constants/app_constants.dart';
import '../storage/secure_storage.dart';

/// Dio HTTP client with JWT injection and error handling.
final dioClientProvider = Provider<DioClient>((ref) {
  return DioClient(ref);
});

class DioClient {
  late final Dio _dio;
  final Ref _ref;

  DioClient(this._ref) {
    _dio = Dio(BaseOptions(
      baseUrl: AppConfig.apiBaseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 30),
      headers: {'Content-Type': 'application/json'},
    ));

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: _attachToken,
      onError: _handleError,
    ));
  }

  Future<void> _attachToken(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final storage = _ref.read(secureStorageProvider);
    final token = await storage.getToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  void _handleError(DioException e, ErrorInterceptorHandler handler) {
    if (e.response?.statusCode == 401) {
      // Token expired — clear and navigate to login is handled by GoRouter redirect
      _ref.read(secureStorageProvider).clearAll();
    }
    handler.next(e);
  }

  /// Unwraps the backend's `{ data: ... }` envelope.
  T unwrap<T>(Response response) {
    final body = response.data;
    if (body is Map<String, dynamic> && body.containsKey('data')) {
      return body['data'] as T;
    }
    return body as T;
  }

  Future<T> get<T>(String path, {Map<String, dynamic>? params}) async {
    final res = await _dio.get<Map<String, dynamic>>(path, queryParameters: params);
    return unwrap<T>(res);
  }

  Future<T> post<T>(String path, {dynamic data}) async {
    final res = await _dio.post<Map<String, dynamic>>(path, data: data);
    return unwrap<T>(res);
  }

  Future<T> patch<T>(String path, {dynamic data}) async {
    final res = await _dio.patch<Map<String, dynamic>>(path, data: data);
    return unwrap<T>(res);
  }

  Future<T> postFormData<T>(String path, FormData formData) async {
    final res = await _dio.post<Map<String, dynamic>>(path, data: formData);
    return unwrap<T>(res);
  }

  Dio get raw => _dio;
}
