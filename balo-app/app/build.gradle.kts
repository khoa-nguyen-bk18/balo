plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.google.services)
    alias(libs.plugins.firebase.crashlytics)
    alias(libs.plugins.firebase.perf)
    alias(libs.plugins.firebase.appdistribution)
}

android {
    namespace = "com.devindie.balo"
    compileSdk {
        version = release(37)
    }

    defaultConfig {
        applicationId = "com.devindie.balo"
        minSdk = 26
        targetSdk = 37
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            optimization {
                enable = true
                packageScope = setOf("androidx.**", "kotlin.**", "kotlinx.**")
            }
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    buildFeatures {
        compose = true
    }
}

dependencies {
    implementation(platform(libs.firebase.bom))
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.ui.graphics)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)

    // Firebase Modules (:api and :impl)
    implementation(project(":firebase:auth:api"))
    implementation(project(":firebase:auth:impl"))
    implementation(project(":firebase:analytics:api"))
    implementation(project(":firebase:analytics:impl"))
    implementation(project(":firebase:performance:api"))
    implementation(project(":firebase:performance:impl"))
    implementation(project(":firebase:phone-verification:api"))
    implementation(project(":firebase:phone-verification:impl"))
    implementation(project(":firebase:firestore:api"))
    implementation(project(":firebase:firestore:impl"))
    implementation(project(":firebase:functions:api"))
    implementation(project(":firebase:functions:impl"))
    implementation(project(":firebase:messaging:api"))
    implementation(project(":firebase:messaging:impl"))
    implementation(project(":firebase:crashlytics:api"))
    implementation(project(":firebase:crashlytics:impl"))

    testImplementation(libs.junit)
    androidTestImplementation(platform(libs.androidx.compose.bom))
    androidTestImplementation(libs.androidx.compose.ui.test.junit4)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(libs.androidx.junit)
    debugImplementation(libs.androidx.compose.ui.test.manifest)
    debugImplementation(libs.androidx.compose.ui.tooling)
}