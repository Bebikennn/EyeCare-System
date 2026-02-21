import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../services/api.dart';
import 'user_session.dart';
import 'package:image_picker/image_picker.dart';
import 'change_password_screen.dart';
import '../widgets/responsive.dart';

/// Profile screen revised for:
/// "EyeCare: An Intelligent Eye Disease Risk Assessment System Using User Health and Habit Data through LightGBM and Rule-Based Approach."
///
/// - Hybrid design (Design #1 header + Design #3 metrics)
/// - Thesis-aligned fields (habits, family history, sunglasses, etc.)
/// - AI Risk Summary (real assessment data from database)
/// - Editable fields, Save button

// ---------------------------
// USER PROFILE MODEL (THESIS-ALIGNED)
// ---------------------------
class UserProfile {
  String name;
  final String email;

  int? age;
  String phone;
  String address;
  String profilePictureUrl; // URL to profile picture

  // Health & Habit Data (Aligned to EyeCare Thesis)
  double? sleepHours; // e.g., 6.5 hrs
  double? screenTime; // hours/day
  bool? familyHistoryEyeDisease;
  bool? smoker;
  int? waterIntake; // glasses/day
  String? activityLevel; // Low, Moderate, High
  String? dietQuality; // Poor, Average, Healthy
  bool? usesSunglasses; // UV protection

  UserProfile({
    required this.name,
    required this.email,
    this.age,
    required this.phone,
    required this.address,
    this.profilePictureUrl = '',
    this.sleepHours,
    this.screenTime,
    this.familyHistoryEyeDisease,
    this.smoker,
    this.waterIntake,
    this.activityLevel,
    this.dietQuality,
    this.usesSunglasses,
  });

  UserProfile copyWith({
    String? name,
    int? age,
    String? phone,
    String? address,
    String? profilePictureUrl,
    double? sleepHours,
    double? screenTime,
    bool? familyHistoryEyeDisease,
    bool? smoker,
    int? waterIntake,
    String? activityLevel,
    String? dietQuality,
    bool? usesSunglasses,
  }) {
    return UserProfile(
      name: name ?? this.name,
      email: email,
      age: age ?? this.age,
      phone: phone ?? this.phone,
      address: address ?? this.address,
      profilePictureUrl: profilePictureUrl ?? this.profilePictureUrl,
      sleepHours: sleepHours ?? this.sleepHours,
      screenTime: screenTime ?? this.screenTime,
      familyHistoryEyeDisease:
          familyHistoryEyeDisease ?? this.familyHistoryEyeDisease,
      smoker: smoker ?? this.smoker,
      waterIntake: waterIntake ?? this.waterIntake,
      activityLevel: activityLevel ?? this.activityLevel,
      dietQuality: dietQuality ?? this.dietQuality,
      usesSunglasses: usesSunglasses ?? this.usesSunglasses,
    );
  }
}

// ---------------------------
// PROFILE SCREEN (REVISED HYBRID)
// ---------------------------
class ProfileScreen extends StatefulWidget {
  final ValueChanged<String> setCurrentScreen;

  const ProfileScreen({Key? key, required this.setCurrentScreen})
    : super(key: key);

  @override
  _ProfileScreenState createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  // Initial profile - will be loaded from database
  UserProfile? userProfile;
  bool isLoading = true;
  String errorMessage = '';

  bool isEditingPersonalInfo = false;
  late UserProfile editProfile;

  // AI result placeholders - loaded from most recent assessment
  bool showAiResult = false;
  String predictedDisease = "No assessment yet";
  double predictedConfidence = 0.0;
  Map<String, dynamic>? recentAssessment; // Store recent assessment data
  Map<String, double> perDiseaseScores = {};

  // Profile picture upload
  XFile? _selectedProfileImage;
  Uint8List? _selectedProfileImageBytes;
  bool _isUploadingProfilePicture = false;
  final ImagePicker _imagePicker = ImagePicker();

  // Model disease classes (aligned to New_data.csv)
  final List<String> diseases = [
    "Astigmatism",
    "Blurred Vision",
    "Dry Eye",
    "Hyperopia",
    "Light Sensitivity",
    "Myopia",
    "Presbyopia",
  ];

  @override
  void initState() {
    super.initState();
    // seed per-disease map with zeros
    perDiseaseScores = {for (var d in diseases) d: 0.0};
    loadUserData();
  }

  Future<void> loadUserData() async {
    setState(() {
      isLoading = true;
      errorMessage = '';
    });

    try {
      final userId = UserSession().userId;
      if (userId == null || userId.isEmpty) {
        setState(() {
          errorMessage = 'User not logged in';
          isLoading = false;
        });
        return;
      }

      // Fetch user profile from database
      final profileResult = await ApiService.getUserProfile(userId);

      if (profileResult['status'] == 'error') {
        setState(() {
          errorMessage = profileResult['error'] ?? 'Failed to load profile';
          isLoading = false;
        });
        return;
      }

      final userData = profileResult['user'];
      final healthData = profileResult['health'] ?? {};
      final habitData = profileResult['habit'] ?? {};

      // Fetch most recent assessment
      final historyResult = await ApiService.getAssessmentHistory(userId);

      Map<String, dynamic>? recentAssessment;
      if (historyResult['status'] == 'success') {
        final List<dynamic> assessments = historyResult['assessments'] ?? [];
        if (assessments.isNotEmpty) {
          recentAssessment = Map<String, dynamic>.from(assessments[0]);
        }
      }

      setState(() {
        // Map database fields from user, health, and habit tables
        // Helper function to safely convert to double (returns null if not available)
        double? toDouble(dynamic value) {
          if (value == null) return null;
          if (value is num) return value.toDouble();
          if (value is String) return double.tryParse(value);
          return null;
        }

        // Helper function to safely convert to int (returns null if not available)
        int? toInt(dynamic value) {
          if (value == null) return null;
          if (value is int) return value;
          if (value is num) return value.toInt();
          if (value is String) return int.tryParse(value);
          return null;
        }

        // Helper function to convert to bool (returns null if not available)
        bool? toBool(dynamic value) {
          if (value == null) return null;
          if (value is bool) return value;
          if (value == 1 ||
              value == '1' ||
              value == 'Yes' ||
              value == 'yes' ||
              value == 'true')
            return true;
          if (value == 0 ||
              value == '0' ||
              value == 'No' ||
              value == 'no' ||
              value == 'false')
            return false;
          return null;
        }

        userProfile = UserProfile(
          name: userData['full_name'] ?? userData['username'] ?? 'User',
          email: userData['email'] ?? '',
          age: toInt(healthData['age']),
          phone: userData['phone'] ?? userData['phone_number'] ?? '',
          address: userData['address'] ?? '',
          profilePictureUrl: userData['profile_picture_url'] ?? '',
          sleepHours: toDouble(habitData['sleep_hours']),
          screenTime: toDouble(habitData['screen_time_hours']),
          familyHistoryEyeDisease: toBool(habitData['family_history']),
          smoker:
              toBool(habitData['smoking_status']) ??
              toBool(habitData['smoker']),
          waterIntake: () {
            final waterLiters = toDouble(habitData['water_intake_liters']);
            return waterLiters != null ? (waterLiters * 4).toInt() : null;
          }(),
          activityLevel: habitData['physical_activity_level']?.toString(),
          dietQuality: () {
            final dietVal = habitData['diet_quality'];
            if (dietVal == null) return null;
            final dietInt = toInt(dietVal);
            if (dietInt == null) return null;
            if (dietInt > 6) return 'Healthy';
            if (dietInt > 4) return 'Average';
            return 'Poor';
          }(),
          usesSunglasses:
              toBool(habitData['glasses_usage']) ??
              toBool(habitData['uses_sunglasses']),
        );

        editProfile = userProfile!.copyWith();

        // Store recent assessment data to state variable
        this.recentAssessment = recentAssessment;

        // Load recent assessment data if available
        if (recentAssessment != null) {
          print('Recent assessment data: $recentAssessment'); // Debug

          predictedDisease =
              recentAssessment['predicted_disease'] ?? 'No assessment';

          // Parse confidence score
          final confRaw = recentAssessment['confidence_score'];
          if (confRaw != null) {
            double conf = 0.0;
            if (confRaw is num) {
              conf = confRaw.toDouble();
            } else if (confRaw is String) {
              conf = double.tryParse(confRaw) ?? 0.0;
            }
            // If between 0-1, multiply by 100
            if (conf > 0 && conf <= 1) {
              conf = conf * 100;
            }
            predictedConfidence = conf;
          }

          // Show AI result if we have a disease prediction
          if (predictedDisease != 'No assessment' &&
              predictedDisease.isNotEmpty) {
            showAiResult = true;
          }

          // Parse disease probabilities if available
          final probsData = recentAssessment['disease_probabilities'];
          print('Disease probabilities data: $probsData'); // Debug

          if (probsData != null) {
            try {
              Map<String, dynamic> probs;
              if (probsData is String) {
                probs = Map<String, dynamic>.from(jsonDecode(probsData));
              } else if (probsData is Map) {
                probs = Map<String, dynamic>.from(probsData);
              } else {
                probs = {};
              }

              // Convert to double map and normalize to 0-1 range
              perDiseaseScores = {};
              probs.forEach((key, value) {
                double val = 0.0;
                if (value is num) {
                  val = value.toDouble();
                } else if (value is String) {
                  val = double.tryParse(value) ?? 0.0;
                }
                // Normalize to 0-1 if needed
                if (val > 1) {
                  val = val / 100;
                }
                perDiseaseScores[key] = val;
              });

              print('Parsed disease scores: $perDiseaseScores'); // Debug
            } catch (e) {
              print('Error parsing disease probabilities: $e');
            }
          }
        }

        isLoading = false;
      });
    } catch (e) {
      setState(() {
        errorMessage = 'Error loading profile: $e';
        isLoading = false;
      });
    }
  }

  void handleSavePersonalInfo() async {
    // Save to database
    try {
      final userId = UserSession().userId;
      if (userId == null || userId.isEmpty) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('User not logged in')));
        return;
      }

      final updateData = {
        'full_name': editProfile.name,
        'age': editProfile.age,
        'phone_number': editProfile.phone,
        'address': editProfile.address,
        'sleep_hours': editProfile.sleepHours,
        'screen_time': editProfile.screenTime,
        'family_history': editProfile.familyHistoryEyeDisease == true
            ? 1
            : (editProfile.familyHistoryEyeDisease == false ? 0 : null),
        'smoker': editProfile.smoker == true
            ? 1
            : (editProfile.smoker == false ? 0 : null),
        'water_intake': editProfile.waterIntake != null
            ? editProfile.waterIntake! / 4
            : null, // Convert glasses to liters
        'activity_level': editProfile.activityLevel,
        'diet_quality': editProfile.dietQuality,
        'uses_sunglasses': editProfile.usesSunglasses == true
            ? 1
            : (editProfile.usesSunglasses == false ? 0 : null),
      };

      final result = await ApiService.updateUserProfile(userId, updateData);

      if (result['status'] == 'success') {
        setState(() {
          userProfile = editProfile.copyWith();
          isEditingPersonalInfo = false;
        });

        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Personal information updated successfully'),
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to update: ${result['error']}')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Error saving profile: $e')));
    }
  }

  // Pick image from gallery
  Future<void> _pickProfileImage() async {
    try {
      final pickedFile = await _imagePicker.pickImage(
        source: ImageSource.gallery,
        imageQuality: 80,
      );

      if (pickedFile != null) {
        final bytes = await pickedFile.readAsBytes();
        setState(() {
          _selectedProfileImage = pickedFile;
          _selectedProfileImageBytes = bytes;
        });
      }
    } catch (e) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Error picking image: $e')));
    }
  }

  // Take photo from camera
  Future<void> _captureProfileImage() async {
    try {
      final pickedFile = await _imagePicker.pickImage(
        source: ImageSource.camera,
        imageQuality: 80,
      );

      if (pickedFile != null) {
        final bytes = await pickedFile.readAsBytes();
        setState(() {
          _selectedProfileImage = pickedFile;
          _selectedProfileImageBytes = bytes;
        });
      }
    } catch (e) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Error capturing image: $e')));
    }
  }

  // Upload profile picture
  Future<void> _uploadProfilePicture() async {
    if (_selectedProfileImage == null || _selectedProfileImageBytes == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select an image first')),
      );
      return;
    }

    setState(() {
      _isUploadingProfilePicture = true;
    });

    try {
      final userId = UserSession().userId;
      if (userId == null || userId.isEmpty) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('User not logged in')));
        return;
      }

        final imageBytes = _selectedProfileImageBytes!;
      final fileName =
          'profile_${userId}_${DateTime.now().millisecondsSinceEpoch}.jpg';

      final result = await ApiService.uploadProfilePicture(
        userId,
        imageBytes,
        fileName,
      );

      setState(() {
        _isUploadingProfilePicture = false;
      });

      if (result['status'] == 'success') {
        setState(() {
          _selectedProfileImage = null;
          _selectedProfileImageBytes = null;
          // Update the profile picture URL
          if (userProfile != null) {
            userProfile = userProfile!.copyWith(
              profilePictureUrl: result['profile_picture_url'] ?? '',
            );
          }
        });

        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Profile picture uploaded successfully'),
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to upload: ${result['error']}')),
        );
      }
    } catch (e) {
      setState(() {
        _isUploadingProfilePicture = false;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error uploading profile picture: $e')),
      );
    }
  }

  // Risk indicator (UI-only quick heuristic)
  String getRiskStatus() {
    if (userProfile == null) return "Unknown";

    double riskScore = 0;

    if (userProfile!.sleepHours != null && userProfile!.sleepHours! < 7)
      riskScore += 1;
    if (userProfile!.screenTime != null && userProfile!.screenTime! > 6)
      riskScore += 1;
    if (userProfile!.familyHistoryEyeDisease == true) riskScore += 2;
    if (userProfile!.smoker == true) riskScore += 2;
    if (userProfile!.waterIntake != null && userProfile!.waterIntake! < 4)
      riskScore += 1;
    if (userProfile!.activityLevel?.toLowerCase() == "low") riskScore += 1;
    if (userProfile!.dietQuality?.toLowerCase() == "poor") riskScore += 1;
    if (userProfile!.usesSunglasses == false) riskScore += 0.5;

    // If no data available, return Unknown
    if (riskScore == 0 &&
        userProfile!.sleepHours == null &&
        userProfile!.screenTime == null) {
      return "Unknown";
    }

    if (riskScore <= 6) return "Low Risk";
    if (riskScore <= 13) return "Moderate Risk";
    return "High Risk";
  }

  Color getRiskColor() {
    switch (getRiskStatus()) {
      case "Low Risk":
        return Colors.green.shade600;
      case "Moderate Risk":
        return Colors.orange.shade600;
      default:
        return Colors.red.shade600;
    }
  }

  // Small helper to format percent
  String percentStr(double v) => "${(v * 100).toStringAsFixed(0)}%";

  @override
  Widget build(BuildContext context) {
    // Show loading state
    if (isLoading) {
      return Scaffold(
        backgroundColor: Colors.grey.shade50,
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    // Show error state
    if (errorMessage.isNotEmpty || userProfile == null) {
      return Scaffold(
        backgroundColor: Colors.grey.shade50,
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.error_outline, size: 64, color: Colors.red[300]),
                const SizedBox(height: 16),
                Text(
                  errorMessage.isEmpty
                      ? 'Failed to load profile'
                      : errorMessage,
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 16, color: Colors.black54),
                ),
                const SizedBox(height: 24),
                ElevatedButton.icon(
                  onPressed: loadUserData,
                  icon: const Icon(Icons.refresh),
                  label: const Text('Retry'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue,
                    foregroundColor: Colors.white,
                  ),
                ),
              ],
            ),
          ),
        ),
      );
    }

    final risk = getRiskStatus();
    final riskColor = getRiskColor();

    return Scaffold(
      backgroundColor: Colors.grey.shade50,
      body: Column(
        children: [
          // HEADER SECTION (Design 1 preserved)
          Container(
            padding: EdgeInsets.only(
              top: MediaQuery.of(context).padding.top + 16,
              bottom: 24,
            ),
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [Colors.deepPurple, Colors.blue],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.vertical(bottom: Radius.circular(28)),
            ),
            child: Column(
              children: [
                // Navigation Row
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16.0),
                  child: Stack(
                    children: [
                      // Back button on the left
                      IconButton(
                        icon: const Icon(Icons.arrow_back, color: Colors.white),
                        onPressed: () {
                          Navigator.pop(context);
                        },
                      ),
                      // Title in the center
                      const Center(
                        child: Text(
                          'My Profile',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 20,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 16),

                // User Avatar with Upload Functionality
                GestureDetector(
                  onTap: _showImagePickerOptions,
                  child: Stack(
                    children: [
                      Container(
                        width: 96,
                        height: 96,
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(48),
                          border: Border.all(color: Colors.white, width: 3),
                        ),
                        child: _selectedProfileImageBytes != null
                            ? ClipRRect(
                                borderRadius: BorderRadius.circular(48),
                                child: Image.memory(
                                  _selectedProfileImageBytes!,
                                  fit: BoxFit.cover,
                                ),
                              )
                            : (userProfile?.profilePictureUrl != null &&
                                      userProfile!.profilePictureUrl.isNotEmpty
                                  ? ClipRRect(
                                      borderRadius: BorderRadius.circular(48),
                                      child: Image.network(
                                        userProfile!.profilePictureUrl,
                                        fit: BoxFit.cover,
                                        errorBuilder:
                                            (context, error, stackTrace) {
                                              print(
                                                'Error loading image: $error',
                                              ); // Debug
                                              return Icon(
                                                Icons.person,
                                                size: 48,
                                                color: Colors.deepPurple,
                                              );
                                            },
                                      ),
                                    )
                                  : Icon(
                                      Icons.person,
                                      size: 48,
                                      color: Colors.deepPurple,
                                    )),
                      ),
                      // Camera button overlay
                      Positioned(
                        bottom: 0,
                        right: 0,
                        child: Container(
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(
                              color: Colors.deepPurple,
                              width: 2,
                            ),
                          ),
                          padding: const EdgeInsets.all(6),
                          child: const Icon(
                            Icons.camera_alt,
                            color: Colors.deepPurple,
                            size: 18,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 12),

                // Name (always display, edit in card below)
                Text(
                  userProfile?.name ?? 'User',
                  style: const TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),

                const SizedBox(height: 8),

                Text(
                  userProfile?.email ?? '',
                  style: TextStyle(color: Colors.blue.shade100),
                ),

                const SizedBox(height: 12),

                // Upload/Cancel buttons (shown when image selected)
                if (_selectedProfileImage != null) ...[
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 24.0),
                    child: Row(
                      children: [
                        Expanded(
                          child: ElevatedButton.icon(
                            onPressed: _isUploadingProfilePicture
                                ? null
                                : _uploadProfilePicture,
                            icon: _isUploadingProfilePicture
                                ? const SizedBox(
                                    width: 16,
                                    height: 16,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                      valueColor: AlwaysStoppedAnimation<Color>(
                                        Colors.white,
                                      ),
                                    ),
                                  )
                                : const Icon(Icons.cloud_upload),
                            label: Text(
                              _isUploadingProfilePicture
                                  ? 'Uploading...'
                                  : 'Upload Picture',
                            ),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.white,
                              foregroundColor: Colors.deepPurple,
                              padding: const EdgeInsets.symmetric(vertical: 10),
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        ElevatedButton(
                          onPressed: _isUploadingProfilePicture
                              ? null
                              : () {
                                  setState(() {
                                    _selectedProfileImage = null;
                                    _selectedProfileImageBytes = null;
                                  });
                                },
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.white.withValues(
                              alpha: 0.2,
                            ),
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(
                              vertical: 10,
                              horizontal: 14,
                            ),
                          ),
                          child: const Text('Cancel'),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 12),
                ],

                // Risk Badge and quick AI summary row (compact)
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 14,
                        vertical: 8,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.18),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Row(
                        children: [
                          Text(
                            "Eye Health: ",
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          Text(
                            risk,
                            style: TextStyle(
                              color: riskColor,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 12),
                    // small AI chip
                    GestureDetector(
                      onTap: () {
                        // show AI detail modal
                        if (showAiResult) {
                          showAiDetailDialog(context);
                        } else {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text(
                                "No assessment data available. Complete an assessment first.",
                              ),
                            ),
                          );
                        }
                      },
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 6,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.08),
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: Row(
                          children: [
                            const Icon(
                              Icons.smart_toy_outlined,
                              color: Colors.white,
                              size: 16,
                            ),
                            const SizedBox(width: 6),
                            Text(
                              showAiResult
                                  ? "${predictedDisease} (${predictedConfidence.toStringAsFixed(0)}%)"
                                  : "AI: no result",
                              style: const TextStyle(color: Colors.white),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

          // CONTENT SECTION
          Expanded(
            child: ResponsiveScroll(
              maxWidth: 980,
              child: Column(
                children: [
                  // PERSONAL INFORMATION CARD (Editable)
                  Container(
                    padding: const EdgeInsets.all(16),
                    margin: const EdgeInsets.only(bottom: 12),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.grey.withValues(alpha: 0.10),
                          blurRadius: 8,
                          offset: const Offset(0, 3),
                        ),
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Row(
                              children: [
                                Icon(
                                  Icons.person,
                                  color: Colors.blue,
                                  size: 20,
                                ),
                                const SizedBox(width: 8),
                                const Text(
                                  "Personal Information",
                                  style: TextStyle(fontWeight: FontWeight.bold),
                                ),
                              ],
                            ),
                            IconButton(
                              icon: Icon(
                                isEditingPersonalInfo
                                    ? Icons.close
                                    : Icons.edit,
                                color: Colors.blue,
                                size: 20,
                              ),
                              onPressed: () {
                                setState(() {
                                  isEditingPersonalInfo =
                                      !isEditingPersonalInfo;
                                  if (userProfile != null) {
                                    editProfile = userProfile!.copyWith();
                                  }
                                });
                              },
                              tooltip: isEditingPersonalInfo
                                  ? 'Cancel'
                                  : 'Edit',
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        editableRow(
                          label: "Full Name",
                          value: userProfile?.name ?? '',
                          editMode: isEditingPersonalInfo,
                          initialText: editProfile.name,
                          onChanged: (v) => editProfile.name = v,
                        ),
                        editableRow(
                          label: "Age",
                          value: userProfile?.age?.toString() ?? 'N/A',
                          editMode: isEditingPersonalInfo,
                          keyboardType: TextInputType.number,
                          initialText: editProfile.age?.toString() ?? '',
                          onChanged: (v) => editProfile.age = int.tryParse(v),
                        ),
                        editableRow(
                          label: "Phone",
                          value: userProfile?.phone ?? '',
                          editMode: isEditingPersonalInfo,
                          keyboardType: TextInputType.phone,
                          initialText: editProfile.phone,
                          onChanged: (v) => editProfile.phone = v,
                        ),
                        editableRow(
                          label: "Address",
                          value: userProfile?.address ?? '',
                          editMode: isEditingPersonalInfo,
                          keyboardType: TextInputType.streetAddress,
                          initialText: editProfile.address,
                          onChanged: (v) => editProfile.address = v,
                        ),
                        if (isEditingPersonalInfo) ...[
                          const SizedBox(height: 12),
                          SizedBox(
                            width: double.infinity,
                            child: ElevatedButton(
                              onPressed: () => handleSavePersonalInfo(),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.blue,
                                padding: const EdgeInsets.symmetric(
                                  vertical: 12,
                                ),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(8),
                                ),
                              ),
                              child: const Text(
                                "Save Changes",
                                style: TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),

                  const SizedBox(height: 16),

                  // HEALTH & HABITS CARD (Read-only - from assessments)
                  ProfileCard(
                    title: "Health & Habit Data (From Assessment)",
                    icon: Icons.health_and_safety,
                    children: [
                      editableRow(
                        label: "Sleep Hours",
                        value: userProfile?.sleepHours != null
                            ? "${userProfile!.sleepHours!.toStringAsFixed(1)} hrs"
                            : "N/A",
                        editMode: false,
                        onChanged: (v) {},
                      ),
                      editableRow(
                        label: "Daily Screen Time",
                        value: userProfile?.screenTime != null
                            ? "${userProfile!.screenTime!.toStringAsFixed(1)} hrs"
                            : "N/A",
                        editMode: false,
                        onChanged: (v) {},
                      ),
                      toggleRow(
                        label: "Family Eye Disease History",
                        value: userProfile?.familyHistoryEyeDisease ?? false,
                        editMode: false,
                        onToggle: (v) {},
                        showNaWhenNull:
                            userProfile?.familyHistoryEyeDisease == null,
                      ),
                      toggleRow(
                        label: "Smoker",
                        value: userProfile?.smoker ?? false,
                        editMode: false,
                        onToggle: (v) {},
                        showNaWhenNull: userProfile?.smoker == null,
                      ),
                      editableRow(
                        label: "Water Intake (glasses/day)",
                        value: userProfile?.waterIntake != null
                            ? "${userProfile!.waterIntake}"
                            : "N/A",
                        editMode: false,
                        onChanged: (v) {},
                      ),
                      editableRow(
                        label: "Activity Level",
                        value: userProfile?.activityLevel ?? 'N/A',
                        editMode: false,
                        onChanged: (v) {},
                      ),
                      editableRow(
                        label: "Diet Quality",
                        value: userProfile?.dietQuality ?? 'N/A',
                        editMode: false,
                        onChanged: (v) {},
                      ),
                      toggleRow(
                        label: "Uses Sunglasses Outdoors",
                        value: userProfile?.usesSunglasses ?? false,
                        editMode: false,
                        onToggle: (v) {},
                        showNaWhenNull: userProfile?.usesSunglasses == null,
                      ),
                    ],
                  ),

                  const SizedBox(height: 18),

                  // AI Risk Summary (Real Database Data)
                  if (showAiResult)
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(16),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withValues(alpha: 0.04),
                            blurRadius: 6,
                          ),
                        ],
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              const Text(
                                "Latest AI Assessment",
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  fontSize: 16,
                                ),
                              ),
                              OutlinedButton(
                                style: OutlinedButton.styleFrom(
                                  // Some app themes set buttons to take full width
                                  // (minimumSize width = infinity). That breaks when
                                  // the button is placed inside a Row.
                                  minimumSize: const Size(0, 44),
                                ),
                                onPressed: () => showAiDetailDialog(context),
                                child: const Text("View Details"),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          Text(
                            "Results from your most recent eye health assessment",
                            style: TextStyle(
                              color: Colors.grey.shade700,
                              fontSize: 13,
                            ),
                          ),
                          const SizedBox(height: 16),

                          // Predicted Disease Card
                          Container(
                            padding: const EdgeInsets.all(14),
                            decoration: BoxDecoration(
                              color: Colors.blue.shade50,
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(
                                color: Colors.blue.shade200,
                                width: 1.5,
                              ),
                            ),
                            child: Row(
                              children: [
                                Icon(
                                  Icons.medical_services,
                                  color: Colors.blue.shade700,
                                  size: 32,
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        predictedDisease,
                                        style: TextStyle(
                                          fontSize: 16,
                                          fontWeight: FontWeight.bold,
                                          color: Colors.blue.shade900,
                                        ),
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        "Confidence: ${predictedConfidence.toStringAsFixed(1)}%",
                                        style: TextStyle(
                                          fontSize: 14,
                                          color: Colors.blue.shade700,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ),

                          const SizedBox(height: 16),

                          // Top 3 predictions
                          const Divider(),
                          const SizedBox(height: 8),
                          const Text(
                            "Disease Probability Breakdown",
                            style: TextStyle(
                              fontWeight: FontWeight.w600,
                              fontSize: 14,
                            ),
                          ),
                          const SizedBox(height: 12),
                          ...perDiseaseScores.entries
                              .toList()
                              .sortedByValueDesc()
                              .take(3)
                              .map(
                                (e) => Padding(
                                  padding: const EdgeInsets.symmetric(
                                    vertical: 8.0,
                                  ),
                                  child: Row(
                                    children: [
                                      Expanded(
                                        child: Text(
                                          e.key,
                                          style: const TextStyle(fontSize: 13),
                                        ),
                                      ),
                                      const SizedBox(width: 8),
                                      SizedBox(
                                        width: 100,
                                        child: LinearProgressIndicator(
                                          value: e.value,
                                          minHeight: 8,
                                          backgroundColor: Colors.grey.shade200,
                                          color: _scoreColor(e.value),
                                        ),
                                      ),
                                      const SizedBox(width: 8),
                                      SizedBox(
                                        width: 45,
                                        child: Text(
                                          percentStr(e.value),
                                          textAlign: TextAlign.right,
                                          style: const TextStyle(fontSize: 13),
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                        ],
                      ),
                    ),

                  if (showAiResult) const SizedBox(height: 18),

                  // VIEW ASSESSMENT ANSWERS BUTTON
                  if (recentAssessment != null)
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        onPressed: () => showAssessmentAnswersDialog(context),
                        icon: const Icon(Icons.quiz),
                        label: const Text(
                          "View Assessment Answers",
                          style: TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.purple,
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                      ),
                    ),

                  if (recentAssessment != null) const SizedBox(height: 12),

                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: () {
                        if (userProfile != null) {
                          showGeneralDialog(
                            context: context,
                            barrierDismissible: true,
                            barrierLabel: 'Dismiss',
                            barrierColor: Colors.black54,
                            transitionDuration: const Duration(
                              milliseconds: 300,
                            ),
                            pageBuilder:
                                (context, animation, secondaryAnimation) {
                                  return Center(
                                    child: Material(
                                      color: Colors.transparent,
                                      child: ChangePasswordScreen(
                                        email: userProfile!.email,
                                      ),
                                    ),
                                  );
                                },
                            transitionBuilder:
                                (
                                  context,
                                  animation,
                                  secondaryAnimation,
                                  child,
                                ) {
                                  return ScaleTransition(
                                    scale: CurvedAnimation(
                                      parent: animation,
                                      curve: Curves.easeOutBack,
                                    ),
                                    child: FadeTransition(
                                      opacity: animation,
                                      child: child,
                                    ),
                                  );
                                },
                          );
                        }
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.blue,
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      child: const Text(
                        "Change Password",
                        style: TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(height: 12),

                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: () {
                        // Navigate back to the LoginScreen
                        Navigator.pushReplacementNamed(context, '/login');
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.red,
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      child: const Text(
                        "Logout",
                        style: TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  // score color helper
  Color _scoreColor(double v) {
    if (v < 0.33) return Colors.green.shade600;
    if (v < 0.66) return Colors.orange.shade600;
    return Colors.red.shade600;
  }

  // Show image picker options
  void _showImagePickerOptions() {
    showModalBottomSheet(
      context: context,
      builder: (BuildContext context) {
        return Container(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                'Select Profile Picture',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 20),
              ListTile(
                leading: const Icon(Icons.camera_alt, color: Colors.blue),
                title: const Text('Take a Photo'),
                onTap: () {
                  Navigator.pop(context);
                  _captureProfileImage();
                },
              ),
              ListTile(
                leading: const Icon(Icons.photo_library, color: Colors.blue),
                title: const Text('Choose from Gallery'),
                onTap: () {
                  Navigator.pop(context);
                  _pickProfileImage();
                },
              ),
              const SizedBox(height: 10),
            ],
          ),
        );
      },
    );
  }

  // Show a dialog with full per-disease breakdown
  void showAiDetailDialog(BuildContext ctx) {
    showDialog(
      context: ctx,
      builder: (_) {
        final sorted = perDiseaseScores.entries.toList()
          ..sort((a, b) => b.value.compareTo(a.value));
        return AlertDialog(
          title: const Text("AI Assessment Details"),
          content: SizedBox(
            width: double.maxFinite,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text("Predicted: $predictedDisease"),
                const SizedBox(height: 6),
                Text("Confidence: ${predictedConfidence.toStringAsFixed(0)}%"),
                const SizedBox(height: 12),
                Expanded(
                  child: ListView(
                    shrinkWrap: true,
                    children: sorted.map((e) {
                      return Padding(
                        padding: const EdgeInsets.symmetric(vertical: 6.0),
                        child: Row(
                          children: [
                            Expanded(child: Text(e.key)),
                            const SizedBox(width: 8),
                            SizedBox(
                              width: 140,
                              child: LinearProgressIndicator(
                                value: e.value,
                                minHeight: 10,
                                color: _scoreColor(e.value),
                                backgroundColor: Colors.grey.shade200,
                              ),
                            ),
                            const SizedBox(width: 8),
                            Text(percentStr(e.value)),
                          ],
                        ),
                      );
                    }).toList(),
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text("Close"),
            ),
          ],
        );
      },
    );
  }

  // Show assessment answers dialog with animation
  void showAssessmentAnswersDialog(BuildContext ctx) {
    showGeneralDialog(
      context: ctx,
      barrierDismissible: true,
      barrierLabel: MaterialLocalizations.of(ctx).modalBarrierDismissLabel,
      barrierColor: Colors.black.withValues(alpha: 0.5),
      transitionDuration: const Duration(milliseconds: 400),
      pageBuilder: (context, animation1, animation2) {
        return const SizedBox();
      },
      transitionBuilder: (context, animation1, animation2, widget) {
        return ScaleTransition(
          scale: Tween<double>(begin: 0.0, end: 1.0).animate(
            CurvedAnimation(parent: animation1, curve: Curves.elasticOut),
          ),
          child: AlertDialog(
            title: Row(
              children: [
                const Icon(Icons.assignment, color: Colors.purple),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    "Assessment Answers${recentAssessment != null && recentAssessment!['created_at'] != null ? ' (${formatAssessmentDate(recentAssessment!['created_at'].toString())})' : ''}",
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
            content: SizedBox(
              width: double.maxFinite,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Expanded(
                    child: SingleChildScrollView(
                      child: _buildAssessmentAnswers(),
                    ),
                  ),
                ],
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text("Close"),
              ),
            ],
          ),
        );
      },
    );
  }

  // Build assessment answers list from database
  Widget _buildAssessmentAnswers() {
    if (recentAssessment == null) {
      return const Center(child: Text("No assessment data available"));
    }

    // Extract and parse assessment_data from recentAssessment
    Map<String, dynamic> assessmentAnswers = {};
    try {
      final assessmentDataRaw = recentAssessment!['assessment_data'];
      if (assessmentDataRaw != null) {
        if (assessmentDataRaw is String) {
          assessmentAnswers = Map<String, dynamic>.from(
            jsonDecode(assessmentDataRaw),
          );
        } else if (assessmentDataRaw is Map) {
          assessmentAnswers = Map<String, dynamic>.from(assessmentDataRaw);
        }
      }
      print('Parsed assessment answers: $assessmentAnswers'); // Debug
    } catch (e) {
      print('Error parsing assessment_data: $e');
    }

    // final symptoms = recentAssessment!['symptoms'] ?? 'Not specified';
    final riskScore = recentAssessment!['risk_score'] ?? 'N/A';
    final riskLevel = recentAssessment!['risk_level'] ?? 'N/A';

    // List of 20 assessment questions (matching assessment_screen.dart)
    final List<Map<String, String>> assessmentQuestions = [
      {"id": "Age", "question": "What is your age?"},
      {"id": "Gender", "question": "What is your gender?"},
      {"id": "BMI", "question": "BMI (Body Mass Index)"},
      {"id": "Screen_Time_Hours", "question": "Daily screen time (hours)?"},
      {"id": "Sleep_Hours", "question": "Sleep hours per night?"},
      {"id": "Smoker", "question": "Do you smoke?"},
      {"id": "Alcohol_Use", "question": "Do you drink alcohol?"},
      {"id": "Diabetes", "question": "Do you have diabetes?"},
      {"id": "Hypertension", "question": "Do you have hypertension?"},
      {
        "id": "Family_History_Eye_Disease",
        "question": "Family history of eye disease?",
      },
      {"id": "Eye_Pain_Frequency", "question": "Eye pain frequency per week?"},
      {"id": "Blurry_Vision_Score", "question": "Blurry vision score (1–10)?"},
      {
        "id": "Light_Sensitivity",
        "question": "Are you sensitive to bright light?",
      },
      {"id": "Eye_Strains_Per_Day", "question": "Eye strain episodes per day?"},
      {
        "id": "Outdoor_Exposure_Hours",
        "question": "Outdoor exposure (hours/day)?",
      },
      {"id": "Diet_Score", "question": "How healthy is your diet? (1–10)"},
      {"id": "Water_Intake_Liters", "question": "Water intake (liters/day)?"},
      {"id": "Glasses_Usage", "question": "Do you use prescription glasses?"},
      {"id": "Previous_Eye_Surgery", "question": "Previous eye surgery?"},
      {"id": "Physical_Activity_Level", "question": "Physical activity level?"},
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Assessment metadata
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.purple.shade50,
            borderRadius: BorderRadius.circular(8),
          ),
          margin: const EdgeInsets.only(bottom: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.description, color: Colors.purple),
                  const SizedBox(width: 8),
                  const Text(
                    "Predicted Disease: ",
                    style: TextStyle(fontWeight: FontWeight.w600),
                  ),
                  Expanded(
                    child: Text(
                      recentAssessment!['predicted_disease'] ?? 'Unknown',
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  const Icon(Icons.flag, color: Colors.purple),
                  const SizedBox(width: 8),
                  const Text(
                    "Risk Level: ",
                    style: TextStyle(fontWeight: FontWeight.w600),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: riskLevel == 'Low'
                          ? Colors.green
                          : (riskLevel == 'Moderate'
                                ? Colors.orange
                                : Colors.red),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      riskLevel.toString(),
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  const Icon(Icons.show_chart, color: Colors.purple),
                  const SizedBox(width: 8),
                  const Text(
                    "Risk Score: ",
                    style: TextStyle(fontWeight: FontWeight.w600),
                  ),
                  Text(
                    riskScore.toString(),
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                ],
              ),
            ],
          ),
        ),

        // Questions and answers
        const Text(
          "Assessment Answers:",
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
        ),
        const SizedBox(height: 12),
        ...List.generate(assessmentQuestions.length, (index) {
          final questionData = assessmentQuestions[index];
          final questionId = questionData['id']!;
          final questionText = questionData['question']!;

          // Get answer from assessment data
          dynamic answer = assessmentAnswers[questionId] ?? 'Not answered';

          // Format answer for better display
          String displayAnswer;
          if (answer == 0 || answer == '0' || answer == false) {
            displayAnswer = answer is bool ? 'No' : answer.toString();
          } else if (answer == 1 || answer == '1' || answer == true) {
            displayAnswer = answer is bool ? 'Yes' : answer.toString();
          } else if (answer is num) {
            displayAnswer = answer
                .toStringAsFixed(2)
                .replaceAll(RegExp(r'\.?0*$'), '');
          } else {
            displayAnswer = answer.toString();
          }

          return Container(
            margin: const EdgeInsets.only(bottom: 12),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.grey.shade50,
              borderRadius: BorderRadius.circular(8),
              border: Border(
                left: BorderSide(color: Colors.purple.shade300, width: 4),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      width: 28,
                      height: 28,
                      decoration: BoxDecoration(
                        color: Colors.purple,
                        borderRadius: BorderRadius.circular(50),
                      ),
                      child: Center(
                        child: Text(
                          '${index + 1}',
                          style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                            fontSize: 12,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        questionText,
                        style: const TextStyle(
                          fontWeight: FontWeight.w600,
                          fontSize: 13,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Row(
                    children: [
                      const Icon(
                        Icons.check_circle,
                        color: Colors.green,
                        size: 16,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          displayAnswer,
                          style: TextStyle(
                            color: Colors.grey.shade800,
                            fontSize: 13,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          );
        }),
      ],
    );
  }

  // ---------------------------
  // REUSABLE UI COMPONENTS
  // ---------------------------

  Widget editableRow({
    required String label,
    required String value,
    required bool editMode,
    required ValueChanged<String> onChanged,
    TextInputType keyboardType = TextInputType.text,
    String? initialText,
  }) {
    final controller = TextEditingController(text: initialText ?? value);
    final isNaValue = value == 'N/A';
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Flexible(
            child: Text(
              label,
              style: const TextStyle(color: Colors.grey, fontSize: 14),
            ),
          ),
          const SizedBox(width: 8),
          ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 180),
            child: editMode
                ? TextField(
                    controller: controller,
                    onChanged: onChanged,
                    keyboardType: keyboardType,
                    textAlign: TextAlign.right,
                    style: const TextStyle(fontWeight: FontWeight.w600),
                    decoration: InputDecoration(
                      isDense: true,
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 10,
                        vertical: 8,
                      ),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                  )
                : Text(
                    value,
                    textAlign: TextAlign.right,
                    style: TextStyle(
                      fontWeight: FontWeight.w600,
                      color: isNaValue ? Colors.grey : Colors.black,
                    ),
                  ),
          ),
        ],
      ),
    );
  }

  Widget toggleRow({
    required String label,
    required bool value,
    required bool editMode,
    required ValueChanged<bool> onToggle,
    bool showNaWhenNull = false,
  }) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Flexible(
            child: Text(
              label,
              style: const TextStyle(color: Colors.grey, fontSize: 14),
            ),
          ),
          const SizedBox(width: 8),
          editMode
              ? Switch(value: value, onChanged: onToggle)
              : Text(
                  showNaWhenNull ? "N/A" : (value ? "Yes" : "No"),
                  style: TextStyle(
                    fontWeight: FontWeight.w600,
                    color: showNaWhenNull ? Colors.grey : Colors.black,
                  ),
                ),
        ],
      ),
    );
  }

  // Format assessment date to readable format
  String formatAssessmentDate(String dateStr) {
    try {
      final date = DateTime.parse(dateStr);
      return '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')} ${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
    } catch (e) {
      return dateStr;
    }
  }
}

// ---------------------------
// PROFILE CARD WIDGET
// ---------------------------
class ProfileCard extends StatelessWidget {
  final String title;
  final IconData icon;
  final List<Widget> children;

  const ProfileCard({
    Key? key,
    required this.title,
    required this.icon,
    required this.children,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withValues(alpha: 0.10),
            blurRadius: 8,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: Colors.blue, size: 20),
              const SizedBox(width: 8),
              Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
            ],
          ),
          const SizedBox(height: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: children,
          ),
        ],
      ),
    );
  }
}

// ---------------------------
// Extension helper to sort Map entries by value desc
// ---------------------------
extension _SortMapEntries on List<MapEntry<String, double>> {
  List<MapEntry<String, double>> sortedByValueDesc() {
    sort((a, b) => b.value.compareTo(a.value));
    return this;
  }
}
