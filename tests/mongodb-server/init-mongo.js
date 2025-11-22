db = db.getSiblingDB('vrecom_test');

db.createCollection('interactions');

db.interactions.createIndex({ user_id: 1 });
db.interactions.createIndex({ item_id: 1 });
db.interactions.createIndex({ timestamp: 1 });
db.interactions.createIndex({ user_id: 1, item_id: 1 }, { unique: true });

print('Database initialized: vrecom_test');
print('Collection created: interactions');
print('Indexes created successfully');
