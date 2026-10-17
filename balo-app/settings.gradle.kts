pluginManagement {
    repositories {
        google {
            content {
                includeGroupByRegex("com\\.android.*")
                includeGroupByRegex("com\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
        mavenCentral()
        gradlePluginPortal()
    }
}
plugins {
    id("org.gradle.toolchains.foojay-resolver-convention") version "1.0.0"
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "Balo"
include(":app")

// Firebase Authentication
include(":firebase:auth:api")
include(":firebase:auth:impl")

// Firebase Analytics
include(":firebase:analytics:api")
include(":firebase:analytics:impl")

// Firebase Performance
include(":firebase:performance:api")
include(":firebase:performance:impl")

// Firebase Phone Number Verification
include(":firebase:phone-verification:api")
include(":firebase:phone-verification:impl")

// Cloud Firestore
include(":firebase:firestore:api")
include(":firebase:firestore:impl")

// Cloud Function
include(":firebase:functions:api")
include(":firebase:functions:impl")

// FCM (Firebase Cloud Messaging)
include(":firebase:messaging:api")
include(":firebase:messaging:impl")

// Firebase Crashlytics
include(":firebase:crashlytics:api")
include(":firebase:crashlytics:impl")
