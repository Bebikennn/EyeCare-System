class UserSession {
  static final UserSession _instance = UserSession._internal();

  String? userId;
  String? username;
  String? email;

  factory UserSession() => _instance;

  UserSession._internal();

  void setUser({required String id, required String name, String? userEmail}) {
    userId = id;
    username = name;
    email = userEmail;
  }

  void clearUser() {
    userId = null;
    username = null;
    email = null;
  }

  bool get isLoggedIn => userId != null && username != null;
}
