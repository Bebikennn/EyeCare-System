import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../services/notification_service.dart' as notif_service;
import 'user_session.dart';
import '../widgets/responsive.dart';
import 'style/app_colors.dart';
import 'style/app_text_styles.dart';

class NotificationScreen extends StatefulWidget {
  const NotificationScreen({Key? key}) : super(key: key);

  @override
  State<NotificationScreen> createState() => _NotificationScreenState();
}

class _NotificationScreenState extends State<NotificationScreen> {
  final notif_service.NotificationService _notificationService =
      notif_service.NotificationService();
  late Future<void> _loadNotificationsFuture;

  List<notif_service.Notification> _notifications = [];
  int _unreadCount = 0;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _loadNotificationsFuture = _loadNotifications();
  }

  Future<void> _loadNotifications() async {
    if (!mounted) return;

    setState(() {
      _isLoading = true;
    });

    try {
      final userId = UserSession().userId;
      if (userId == null || userId.isEmpty) {
        setState(() {
          _isLoading = false;
        });
        return;
      }

      final response = await _notificationService.getUserNotifications(userId);

      if (mounted && response.success) {
        setState(() {
          _notifications = response.notifications;
          _unreadCount = response.unreadCount;
          _isLoading = false;
        });
      } else {
        setState(() {
          _isLoading = false;
        });
      }
    } catch (e) {
      print('Error: $e');
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _markAsRead(int index) async {
    final notification = _notifications[index];
    if (notification.isRead) return;

    final userId = UserSession().userId;
    if (userId == null || userId.isEmpty) return;

    final success = await _notificationService.markNotificationAsRead(
      userId,
      notification.notificationId,
    );

    if (success && mounted) {
      setState(() {
        _notifications[index] = notif_service.Notification(
          notificationId: notification.notificationId,
          title: notification.title,
          message: notification.message,
          type: notification.type,
          isRead: true,
          link: notification.link,
          createdAt: notification.createdAt,
        );
        if (_unreadCount > 0) _unreadCount--;
      });
    }
  }

  Future<void> _markAllAsRead() async {
    final userId = UserSession().userId;
    if (userId == null || userId.isEmpty) return;

    final success =
        await _notificationService.markAllNotificationsAsRead(userId);

    if (success && mounted) {
      setState(() {
        _notifications = _notifications
            .map((n) => notif_service.Notification(
                  notificationId: n.notificationId,
                  title: n.title,
                  message: n.message,
                  type: n.type,
                  isRead: true,
                  link: n.link,
                  createdAt: n.createdAt,
                ))
            .toList();
        _unreadCount = 0;
      });
    }
  }

  Color _getNotificationColor(String type) {
    switch (type) {
      case 'success':
        return AppColors.success;
      case 'warning':
        return AppColors.warn;
      case 'error':
        return AppColors.danger;
      default:
        return AppColors.primary;
    }
  }

  Widget _buildTopHeader() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(12, 14, 16, 18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppColors.primary, AppColors.accent],
          begin: Alignment.centerLeft,
          end: Alignment.centerRight,
        ),
        borderRadius: const BorderRadius.only(
          bottomLeft: Radius.circular(24),
          bottomRight: Radius.circular(24),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.06),
            blurRadius: 12,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.arrow_back, color: Colors.white),
            onPressed: () => Navigator.of(context).maybePop(),
          ),
          const SizedBox(width: 4),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Notifications',
                  style: AppTextStyles.heading(20)
                      .copyWith(color: Colors.white),
                ),
                const SizedBox(height: 2),
                const Text(
                  'Your updates and alerts',
                  style: TextStyle(color: Colors.white70, fontSize: 12),
                ),
              ],
            ),
          ),
          if (_unreadCount > 0)
            TextButton(
              onPressed: _markAllAsRead,
              style: TextButton.styleFrom(
                foregroundColor: Colors.white,
                backgroundColor: AppColors.glass,
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: const Text(
                'Mark all read',
                style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: AppColors.card,
          borderRadius: BorderRadius.circular(20),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.03),
              blurRadius: 10,
              offset: const Offset(0, 6),
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 72,
              height: 72,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    AppColors.primary.withValues(alpha: 0.12),
                    AppColors.accent.withValues(alpha: 0.12),
                  ],
                ),
                borderRadius: BorderRadius.circular(16),
              ),
              child: const Icon(
                Icons.notifications_none,
                size: 38,
                color: AppColors.primary,
              ),
            ),
            const SizedBox(height: 14),
            Text(
              'No notifications yet',
              style: AppTextStyles.heading(18),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 6),
            Text(
              'Your notifications will appear here',
              style: AppTextStyles.subtitle.copyWith(color: AppColors.muted),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  String _formatTime(DateTime dateTime) {
    final now = DateTime.now();
    final difference = now.difference(dateTime);

    if (difference.inMinutes < 1) {
      return 'Just now';
    } else if (difference.inMinutes < 60) {
      return '${difference.inMinutes}m ago';
    } else if (difference.inHours < 24) {
      return '${difference.inHours}h ago';
    } else if (difference.inDays < 7) {
      return '${difference.inDays}d ago';
    } else {
      return DateFormat('MMM d').format(dateTime);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bg,
      body: SafeArea(
        child: ResponsiveConstrained(
          maxWidth: 980,
          padding: EdgeInsets.zero,
          child: Column(
            children: [
              _buildTopHeader(),
              Expanded(
                child: FutureBuilder<void>(
                  future: _loadNotificationsFuture,
                  builder: (context, snapshot) {
                    if (_isLoading ||
                        snapshot.connectionState == ConnectionState.waiting) {
                      return const Center(
                        child: CircularProgressIndicator(
                          valueColor:
                              AlwaysStoppedAnimation<Color>(AppColors.accent),
                        ),
                      );
                    }

                    if (_notifications.isEmpty) {
                      return LayoutBuilder(
                        builder: (context, constraints) {
                          final pad = responsivePagePadding(constraints.maxWidth);
                          return Padding(
                            padding: pad,
                            child: _buildEmptyState(),
                          );
                        },
                      );
                    }

                    return RefreshIndicator(
                      onRefresh: _loadNotifications,
                      color: AppColors.accent,
                      child: LayoutBuilder(
                        builder: (context, constraints) {
                          final pad = responsivePagePadding(constraints.maxWidth);
                          return ListView.builder(
                            padding: pad,
                            itemCount: _notifications.length,
                            itemBuilder: (context, index) {
                              final notification = _notifications[index];
                              final color =
                                  _getNotificationColor(notification.type);

                              return GestureDetector(
                                onTap: () => _markAsRead(index),
                                child: Container(
                                  margin:
                                      const EdgeInsets.symmetric(vertical: 6),
                                  decoration: BoxDecoration(
                                    color: notification.isRead
                                        ? AppColors.card
                                        : AppColors.accent
                                            .withValues(alpha: 0.06),
                                    border: Border(
                                      left: BorderSide(color: color, width: 4),
                                      top: BorderSide(
                                          color: Colors.grey.shade200,
                                          width: 1),
                                      right: BorderSide(
                                          color: Colors.grey.shade200,
                                          width: 1),
                                      bottom: BorderSide(
                                          color: Colors.grey.shade200,
                                          width: 1),
                                    ),
                                    borderRadius: BorderRadius.circular(14),
                                    boxShadow: [
                                      BoxShadow(
                                        color:
                                            Colors.black.withValues(alpha: 0.03),
                                        blurRadius: 8,
                                        offset: const Offset(0, 4),
                                      ),
                                    ],
                                  ),
                                  child: Padding(
                                    padding: const EdgeInsets.all(14),
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Row(
                                          mainAxisAlignment:
                                              MainAxisAlignment.spaceBetween,
                                          children: [
                                            Expanded(
                                              child: Column(
                                                crossAxisAlignment:
                                                    CrossAxisAlignment.start,
                                                children: [
                                                  Row(
                                                    children: [
                                                      Expanded(
                                                        child: Text(
                                                          notification.title,
                                                          style: AppTextStyles
                                                              .cardTitle
                                                              .copyWith(
                                                            fontSize: 14,
                                                          ),
                                                          maxLines: 1,
                                                          overflow: TextOverflow
                                                              .ellipsis,
                                                        ),
                                                      ),
                                                      if (!notification.isRead)
                                                        Container(
                                                          margin:
                                                              const EdgeInsets
                                                                  .only(left: 8),
                                                          width: 8,
                                                          height: 8,
                                                          decoration:
                                                              const BoxDecoration(
                                                            color: AppColors
                                                                .accent,
                                                            shape:
                                                                BoxShape.circle,
                                                          ),
                                                        ),
                                                    ],
                                                  ),
                                                  const SizedBox(height: 4),
                                                  Text(
                                                    _formatTime(
                                                        notification.createdAt),
                                                    style: TextStyle(
                                                      fontSize: 12,
                                                      color: Colors
                                                          .grey.shade600,
                                                    ),
                                                  ),
                                                ],
                                              ),
                                            ),
                                            Container(
                                              padding: const EdgeInsets.all(8),
                                              decoration: BoxDecoration(
                                                color:
                                                    color.withValues(alpha: 0.10),
                                                borderRadius:
                                                    BorderRadius.circular(10),
                                              ),
                                              child: Icon(
                                                _getNotificationIcon(
                                                    notification.type),
                                                size: 18,
                                                color: color,
                                              ),
                                            ),
                                          ],
                                        ),
                                        const SizedBox(height: 10),
                                        Text(
                                          notification.message,
                                          style: TextStyle(
                                            fontSize: 13,
                                            color: Colors.grey.shade700,
                                            height: 1.4,
                                          ),
                                          maxLines: 2,
                                          overflow: TextOverflow.ellipsis,
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                              );
                            },
                          );
                        },
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  IconData _getNotificationIcon(String type) {
    switch (type) {
      case 'success':
        return Icons.check_circle;
      case 'warning':
        return Icons.warning;
      case 'error':
        return Icons.error;
      default:
        return Icons.info;
    }
  }
}
