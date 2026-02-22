# Lessons Learned
_Capture lessons from user corrections here to avoid repeating mistakes._

- Implement strict MVVM per Flutter rules. No Riverpod/Bloc/GetX.
- Always verify before marking done.
- Android 14 Health Connect: A `<meta-data android:name="health_permissions" ... />` is not enough. You must also include the `android.intent.action.VIEW_PERMISSION_USAGE` intent filter in `MainActivity` or requests will silently fail with "Needs Updating".
