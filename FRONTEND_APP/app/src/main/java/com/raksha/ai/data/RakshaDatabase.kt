package com.raksha.ai.data

import androidx.room.Database
import androidx.room.RoomDatabase

@Database(entities = [SecurityEventEntity::class], version = 2, exportSchema = false)
abstract class RakshaDatabase : RoomDatabase() { abstract fun events(): SecurityEventDao }
