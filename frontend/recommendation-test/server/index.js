import express from 'express';
import cors from 'cors';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 3001;

app.use(cors());
app.use(express.json());

const DATA_DIR = path.join(__dirname, 'data');
const USERS_FILE = path.join(DATA_DIR, 'users.json');
const PRODUCTS_FILE = path.join(DATA_DIR, 'products.json');
const INTERACTIONS_FILE = path.join(DATA_DIR, 'interactions.json');

await fs.mkdir(DATA_DIR, { recursive: true });

const readJsonFile = async (filePath, defaultValue = []) => {
  try {
    const data = await fs.readFile(filePath, 'utf-8');
    return JSON.parse(data);
  } catch (error) {
    await fs.writeFile(filePath, JSON.stringify(defaultValue, null, 2));
    return defaultValue;
  }
};

const writeJsonFile = async (filePath, data) => {
  await fs.writeFile(filePath, JSON.stringify(data, null, 2));
};

app.post('/api/auth/login', async (req, res) => {
  try {
    const { username } = req.body;

    if (!username) {
      return res.status(400).json({ error: 'Username is required' });
    }

    const users = await readJsonFile(USERS_FILE, []);
    let user = users.find(u => u.username === username);

    if (!user) {
      user = {
        id: `user_${Date.now()}`,
        username,
        createdAt: new Date().toISOString(),
      };
      users.push(user);
      await writeJsonFile(USERS_FILE, users);
    }

    res.json({ user });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.get('/api/products', async (req, res) => {
  try {
    const { category } = req.query;
    let products = await readJsonFile(PRODUCTS_FILE, []);

    if (category && category !== 'all') {
      products = products.filter(p => p.category === category);
    }

    res.json({ products });
  } catch (error) {
    console.error('Get products error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.get('/api/products/categories', async (req, res) => {
  try {
    const products = await readJsonFile(PRODUCTS_FILE, []);
    const categories = [...new Set(products.map(p => p.category))];
    res.json({ categories });
  } catch (error) {
    console.error('Get categories error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.post('/api/interactions', async (req, res) => {
  try {
    const { userId, productId, type, value } = req.body;

    if (!userId || !productId || !type) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    const interactions = await readJsonFile(INTERACTIONS_FILE, []);

    const interaction = {
      id: `interaction_${Date.now()}`,
      userId,
      productId,
      type,
      value: value || null,
      timestamp: new Date().toISOString(),
    };

    interactions.push(interaction);
    await writeJsonFile(INTERACTIONS_FILE, interactions);

    res.json({ interaction });
  } catch (error) {
    console.error('Create interaction error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.get('/api/interactions/:userId', async (req, res) => {
  try {
    const { userId } = req.params;
    const interactions = await readJsonFile(INTERACTIONS_FILE, []);
    const userInteractions = interactions.filter(i => i.userId === userId);
    res.json({ interactions: userInteractions });
  } catch (error) {
    console.error('Get interactions error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.listen(PORT, () => {
  console.log(`Recommendation test server running on http://localhost:${PORT}`);
});
