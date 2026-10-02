plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.google.devtools.ksp")
}

android {
    namespace = "com.raksha.ai"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.raksha.ai"
        minSdk = 26
        targetSdk = 36
        versionCode = 2
        versionName = "1.1.0"
    }

    buildFeatures { buildConfig = true }

    buildTypes {
        debug {
            applicationIdSuffix = ".debug"
            versionNameSuffix = "-debug"
            buildConfigField("String", "BACKEND_BASE_URL", "\"${propertyOrDefault("RAKSHA_BACKEND_URL", "http://127.0.0.1:8000/")}\"")
            buildConfigField("String", "GOOGLE_WEB_CLIENT_ID", "\"${propertyOrDefault("RAKSHA_GOOGLE_WEB_CLIENT_ID", "")}\"")
            buildConfigField("boolean", "EMAIL_SYNC_ENABLED", "true")
        }
        release {
            isMinifyEnabled = false
            buildConfigField("String", "BACKEND_BASE_URL", "\"${propertyOrDefault("RAKSHA_BACKEND_URL", "https://api.example.com/")}\"")
            buildConfigField("String", "GOOGLE_WEB_CLIENT_ID", "\"${propertyOrDefault("RAKSHA_GOOGLE_WEB_CLIENT_ID", "")}\"")
            buildConfigField("boolean", "EMAIL_SYNC_ENABLED", "false")
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }

    packaging {
        resources.excludes += setOf("META-INF/NOTICE.md", "META-INF/LICENSE.md")
    }
}

fun propertyOrDefault(name: String, defaultValue: String): String =
    providers.gradleProperty(name).orNull ?: defaultValue

dependencies {
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("androidx.activity:activity-ktx:1.10.1")
    implementation("com.google.android.material:material:1.12.0")
    implementation("com.google.android.gms:play-services-auth:21.2.0")
    implementation("androidx.recyclerview:recyclerview:1.4.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.9.0")
    implementation("com.squareup.retrofit2:retrofit:2.11.0")
    implementation("com.squareup.retrofit2:converter-gson:2.11.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")
    implementation("androidx.lifecycle:lifecycle-viewmodel-ktx:2.8.7")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.7")
    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    ksp("androidx.room:room-compiler:2.6.1")
    testImplementation("junit:junit:4.13.2")
    testImplementation("androidx.room:room-testing:2.6.1")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.9.0")
}
