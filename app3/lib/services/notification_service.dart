import 'package:http/http.dart' as http;
import 'dart:convert';
import 'api.dart';

class Notification {
  final String notificationId;
  final String title;
  final String message;
  final String type; // info, success, warning, error
  final bool isRead;
  final String? link;
  final DateTime createdAt;

  Notification({
    required this.notificationId,
    required this.title,
    required this.message,
    required this.type,
    required this.isRead,
    this.link,
    required this.createdAt,
  });

  factory Notification.fromJson(Map<String, dynamic> json) {
    return Notification(
      notificationId: json['notification_id'] ?? '',
      title: json['title'] ?? '',
      message: json['message'] ?? '',
      type: json['type'] ?? 'info',
      isRead: json['is_read'] == 1 || json['is_read'] == true,
      link: json['link'],
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'])
          : DateTime.now(),
    );
  }
}

class NotificationResponse {
  final bool success;
  final List<Notification> notifications;
  final int unreadCount;

  NotificationResponse({
    required this.success,
    required this.notifications,
    required this.unreadCount,
  });

  factory NotificationResponse.fromJson(Map<String, dynamic> json) {
    List<Notification> notifications = [];
    if (json['notifications'] != null) {
      notifications = (json['notifications'] as List)
          .map((n) => Notification.fromJson(n))
          .toList();
    }

    return NotificationResponse(
      success: json['status'] == 'success',
      notifications: notifications,
      unreadCount: json['unread_count'] ?? 0,
    );
  }
}

class NotificationService {
  static final NotificationService _instance = NotificationService._internal();

  factory NotificationService() {
    return _instance;
  }

  NotificationService._internal();

  Future<NotificationResponse> getUserNotifications(String userId) async {
    try {
      final baseUrl = ApiService.baseUrl;
      final url = '$baseUrl/api/notifications/user/$userId';

      print('🔔 Fetching notifications for user: $userId');
      print('📍 URL: $url');

      final response = await http.get(
        Uri.parse(url),
        headers: {
          'Content-Type': 'application/json',
        },
      ).timeout(const Duration(seconds: 10));

      print('📊 Response status: ${response.statusCode}');

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        print('✅ Notifications response: $data');
        return NotificationResponse.fromJson(data);
      } else {
        print('❌ Failed to fetch notifications: ${response.body}');
        return NotificationResponse(
          success: false,
          notifications: [],
          unreadCount: 0,
        );
      }
    } catch (e) {
      print('Error fetching notifications: $e');
      return NotificationResponse(
        success: false,
        notifications: [],
        unreadCount: 0,
      );
    }
  }

  Future<bool> markNotificationAsRead(
      String userId, String notificationId) async {
    try {
      final baseUrl = ApiService.baseUrl;
      final url =
          '$baseUrl/api/notifications/user/$userId/$notificationId/mark-read';

      final response = await http.put(
        Uri.parse(url),
        headers: {
          'Content-Type': 'application/json',
        },
      ).timeout(const Duration(seconds: 10));

      return response.statusCode == 200;
    } catch (e) {
      print('Error marking notification as read: $e');
      return false;
    }
  }

  Future<bool> markAllNotificationsAsRead(String userId) async {
    try {
      final baseUrl = ApiService.baseUrl;
      final url = '$baseUrl/api/notifications/user/$userId/mark-all-read';

      final response = await http.put(
        Uri.parse(url),
        headers: {
          'Content-Type': 'application/json',
        },
      ).timeout(const Duration(seconds: 10));

      return response.statusCode == 200;
    } catch (e) {
      print('Error marking all notifications as read: $e');
      return false;
    }
  }

  Future<bool> createNotification({
    required String userId,
    required String title,
    required String message,
    String type = 'info',
    String? link,
  }) async {
    try {
      final baseUrl = ApiService.baseUrl;
      final url = '$baseUrl/api/notifications/user/$userId/create';

      final body = jsonEncode({
        'title': title,
        'message': message,
        'type': type,
        'link': link,
      });

      final response = await http
          .post(
            Uri.parse(url),
            headers: {
              'Content-Type': 'application/json',
            },
            body: body,
          )
          .timeout(const Duration(seconds: 10));

      return response.statusCode == 201;
    } catch (e) {
      print('Error creating notification: $e');
      return false;
    }
  }
}
