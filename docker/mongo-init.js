// MongoDB initialization script
// This runs when the MongoDB container is first started

db = db.getSiblingDB('finanalysis');

// Create app user with read/write access to finanalysis DB
db.createUser({
    user: 'finanalysis_user',
    pwd: 'finanalysis_password',
    roles: [
        { role: 'readWrite', db: 'finanalysis' },
    ],
});

// Create initial collections with schema validation
db.createCollection('users', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['name', 'email', 'password'],
            properties: {
                name: { bsonType: 'string', minLength: 2, maxLength: 50 },
                email: { bsonType: 'string' },
                password: { bsonType: 'string' },
                role: { bsonType: 'string', enum: ['user', 'premium', 'admin'] },
            },
        },
    },
});

db.createCollection('stock_cache');
db.createCollection('news_cache');
db.createCollection('analysis_reports');

// Create indexes
db.users.createIndex({ email: 1 }, { unique: true });
db.stock_cache.createIndex({ symbol: 1, exchange: 1 });
db.stock_cache.createIndex({ updatedAt: 1 }, { expireAfterSeconds: 300 }); // TTL 5 minutes
db.news_cache.createIndex({ symbol: 1 });
db.news_cache.createIndex({ createdAt: 1 }, { expireAfterSeconds: 600 }); // TTL 10 minutes
db.analysis_reports.createIndex({ userId: 1, symbol: 1 });

print('✅ MongoDB finanalysis database initialized successfully!');
