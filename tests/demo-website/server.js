const express = require("express");
const session = require("express-session");
const bodyParser = require("body-parser");
const cookieParser = require("cookie-parser");
const axios = require("axios");
const fs = require("fs").promises;
const path = require("path");

const app = express();
const PORT = process.env.PORT || 3500;
const API_SERVER_URL = process.env.API_SERVER_URL || "http://localhost:2030";

app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(cookieParser());
app.use(express.static("public"));

app.use(
    session({
        secret: "demo-secret-key-change-in-production",
        resave: false,
        saveUninitialized: false,
        cookie: {
            secure: false,
            httpOnly: true,
            maxAge: 24 * 60 * 60 * 1000,
        },
    }),
);

const DATA_DIR = path.join(__dirname, "data");
const USERS_FILE = path.join(DATA_DIR, "users.json");
const PRODUCTS_FILE = path.join(DATA_DIR, "products.json");
const ACTIONS_FILE = path.join(DATA_DIR, "user_actions.json");

async function ensureDataFiles() {
    try {
        await fs.mkdir(DATA_DIR, { recursive: true });

        try {
            await fs.access(USERS_FILE);
        } catch {
            await fs.writeFile(USERS_FILE, JSON.stringify([], null, 2));
        }

        try {
            await fs.access(PRODUCTS_FILE);
        } catch {
            const sampleProducts = [
                {
                    id: 1,
                    name: "Sony WH-1000XM5 Wireless Headphones",
                    description: "Industry-leading noise canceling with Auto NC Optimizer, exceptional sound quality with DSEE Extreme, 30-hour battery life, crystal clear hands-free calling",
                    price: 399.99,
                    category: "electronics",
                    brand: "Sony",
                    stock: 45,
                    rating: 4.8,
                },
                {
                    id: 2,
                    name: "Levi's 501 Original Fit Jeans",
                    description: "The original blue jean since 1873. Made with 100% cotton denim, button fly, straight leg fit, classic 5-pocket styling",
                    price: 89.50,
                    category: "clothing",
                    brand: "Levi's",
                    stock: 120,
                    rating: 4.6,
                },
                {
                    id: 3,
                    name: "Apple MacBook Air 13-inch M2 Chip",
                    description: "Supercharged by M2 chip, 13.6-inch Liquid Retina display, 8GB RAM, 256GB SSD, up to 18 hours battery life, 1080p FaceTime HD camera",
                    price: 1199.00,
                    category: "electronics",
                    brand: "Apple",
                    stock: 28,
                    rating: 4.9,
                },
                {
                    id: 4,
                    name: "Atomic Habits by James Clear",
                    description: "An Easy & Proven Way to Build Good Habits & Break Bad Ones. #1 New York Times bestseller with over 10 million copies sold worldwide",
                    price: 16.99,
                    category: "books",
                    brand: "Penguin Random House",
                    stock: 250,
                    rating: 4.7,
                },
                {
                    id: 5,
                    name: "Samsung 65-inch QLED 4K Smart TV",
                    description: "Quantum Dot technology, 4K UHD resolution, HDR10+, Smart TV with Tizen OS, Alexa built-in, Motion Xcelerator Turbo+",
                    price: 1299.99,
                    category: "electronics",
                    brand: "Samsung",
                    stock: 15,
                    rating: 4.5,
                },
                {
                    id: 6,
                    name: "Nike Air Max 270 Running Shoes",
                    description: "Max Air unit delivers exceptional cushioning, breathable mesh upper, durable rubber outsole, iconic Nike design",
                    price: 150.00,
                    category: "clothing",
                    brand: "Nike",
                    stock: 80,
                    rating: 4.6,
                },
                {
                    id: 7,
                    name: "KitchenAid Artisan Stand Mixer",
                    description: "5-quart stainless steel bowl, 10-speed slide control, 325-watt motor, includes flat beater, dough hook, and wire whip",
                    price: 429.99,
                    category: "home",
                    brand: "KitchenAid",
                    stock: 35,
                    rating: 4.9,
                },
                {
                    id: 8,
                    name: "The Psychology of Money by Morgan Housel",
                    description: "Timeless lessons on wealth, greed, and happiness. Wall Street Journal bestseller with practical insights on managing money",
                    price: 14.99,
                    category: "books",
                    brand: "Harriman House",
                    stock: 180,
                    rating: 4.8,
                },
                {
                    id: 9,
                    name: "Canon EOS R6 Mark II Camera Body",
                    description: "24.2MP full-frame sensor, 40 fps continuous shooting, 6K video recording, advanced subject detection AF",
                    price: 2499.00,
                    category: "electronics",
                    brand: "Canon",
                    stock: 12,
                    rating: 4.9,
                },
                {
                    id: 10,
                    name: "Adidas Ultraboost 22 Women's Sneakers",
                    description: "Energy-returning Boost midsole, Primeknit+ upper, Continental rubber outsole, sustainable materials",
                    price: 190.00,
                    category: "clothing",
                    brand: "Adidas",
                    stock: 65,
                    rating: 4.7,
                },
                {
                    id: 11,
                    name: "Instant Pot Duo 7-in-1 Pressure Cooker",
                    description: "6-quart capacity, 7 appliances in 1: pressure cooker, slow cooker, rice cooker, steamer, saute pan, yogurt maker, and warmer",
                    price: 99.95,
                    category: "home",
                    brand: "Instant Pot",
                    stock: 95,
                    rating: 4.7,
                },
                {
                    id: 12,
                    name: "Educated: A Memoir by Tara Westover",
                    description: "A remarkable story of a woman's quest for knowledge. New York Times bestseller, Bill Gates' favorite book of the year",
                    price: 18.00,
                    category: "books",
                    brand: "Random House",
                    stock: 140,
                    rating: 4.8,
                },
                {
                    id: 13,
                    name: "Dyson V15 Detect Cordless Vacuum",
                    description: "Laser detect technology, LCD screen shows real-time particle count, 60 minutes run time, HEPA filtration",
                    price: 649.99,
                    category: "home",
                    brand: "Dyson",
                    stock: 22,
                    rating: 4.6,
                },
                {
                    id: 14,
                    name: "The North Face Thermoball Jacket",
                    description: "Synthetic insulation stays warm even when wet, water-repellent finish, packable design, lightweight warmth",
                    price: 229.00,
                    category: "clothing",
                    brand: "The North Face",
                    stock: 55,
                    rating: 4.5,
                },
                {
                    id: 15,
                    name: "iPad Pro 12.9-inch M2 Chip",
                    description: "M2 chip with 8-core CPU, 12.9-inch Liquid Retina XDR display, 128GB storage, Apple Pencil hover support",
                    price: 1099.00,
                    category: "electronics",
                    brand: "Apple",
                    stock: 18,
                    rating: 4.9,
                },
            ];
            await fs.writeFile(
                PRODUCTS_FILE,
                JSON.stringify(sampleProducts, null, 2),
            );
        }

        try {
            await fs.access(ACTIONS_FILE);
        } catch {
            await fs.writeFile(ACTIONS_FILE, JSON.stringify([], null, 2));
        }
    } catch (error) {
        console.error("Error ensuring data files:", error);
    }
}

async function readJSONFile(filePath) {
    try {
        const data = await fs.readFile(filePath, "utf8");
        return JSON.parse(data);
    } catch (error) {
        console.error(`Error reading ${filePath}:`, error);
        return [];
    }
}

async function writeJSONFile(filePath, data) {
    try {
        await fs.writeFile(filePath, JSON.stringify(data, null, 2));
    } catch (error) {
        console.error(`Error writing ${filePath}:`, error);
    }
}

function requireAuth(req, res, next) {
    if (!req.session.user) {
        return res.redirect("/login");
    }
    next();
}

app.get("/", (req, res) => {
    if (req.session.user) {
        return res.redirect("/dashboard");
    }
    res.redirect("/login");
});

app.get("/login", (req, res) => {
    if (req.session.user) {
        return res.redirect("/dashboard");
    }
    res.render("login", { error: null });
});

app.post("/login", async (req, res) => {
    const { username, password } = req.body;

    if (!username || !password) {
        return res.render("login", {
            error: "Username and password are required",
        });
    }

    const users = await readJSONFile(USERS_FILE);
    let user = users.find((u) => u.username === username);

    if (!user) {
        user = {
            id: Date.now().toString(),
            username,
            password,
            createdAt: new Date().toISOString(),
        };
        users.push(user);
        await writeJSONFile(USERS_FILE, users);
    } else if (user.password !== password) {
        return res.render("login", { error: "Invalid password" });
    }

    req.session.user = {
        id: user.id,
        username: user.username,
    };

    res.redirect("/dashboard");
});

app.get("/logout", (req, res) => {
    req.session.destroy();
    res.redirect("/login");
});

app.get("/dashboard", requireAuth, async (req, res) => {
    const products = await readJSONFile(PRODUCTS_FILE);
    const userActions = await readJSONFile(ACTIONS_FILE);
    const userLikes = userActions.filter(
        (a) => a.userId === req.session.user.id && a.action === "like",
    );

    res.render("dashboard", {
        user: req.session.user,
        products,
        likedProductIds: userLikes.map((l) => l.productId),
    });
});

app.get("/api/products", async (req, res) => {
    const products = await readJSONFile(PRODUCTS_FILE);
    res.json(products);
});

app.get("/api/products/:id", async (req, res) => {
    const products = await readJSONFile(PRODUCTS_FILE);
    const product = products.find((p) => p.id === parseInt(req.params.id));

    if (!product) {
        return res.status(404).json({ error: "Product not found" });
    }

    if (req.session.user) {
        await logUserAction(req.session.user.id, product.id, "view");
    }

    res.json(product);
});

app.post("/api/products/:id/like", requireAuth, async (req, res) => {
    const productId = parseInt(req.params.id);
    const products = await readJSONFile(PRODUCTS_FILE);
    const product = products.find((p) => p.id === productId);

    if (!product) {
        return res.status(404).json({ error: "Product not found" });
    }

    await logUserAction(req.session.user.id, productId, "like");

    res.json({ success: true, message: "Product liked" });
});

app.delete("/api/products/:id/like", requireAuth, async (req, res) => {
    const productId = parseInt(req.params.id);
    const actions = await readJSONFile(ACTIONS_FILE);

    const filteredActions = actions.filter(
        (a) =>
            !(
                a.userId === req.session.user.id &&
                a.productId === productId &&
                a.action === "like"
            ),
    );

    await writeJSONFile(ACTIONS_FILE, filteredActions);

    res.json({ success: true, message: "Product unliked" });
});

app.get("/api/recommendations", requireAuth, async (req, res) => {
    try {
        const modelId = req.query.model_id || "model_test";
        const n = req.query.n || "5";

        const response = await axios.get(`${API_SERVER_URL}/api/v1/recommend`, {
            params: {
                user_id: req.session.user.id,
                model_id: modelId,
                n: n,
            },
            headers: {
                Authorization: req.headers.authorization || "",
            },
            timeout: 10000,
        });

        // Transform API response to frontend format
        const apiData = response.data;
        let recommendations = [];

        // Extract recommendations from predictions object
        if (apiData.predictions && apiData.predictions[req.session.user.id]) {
            recommendations = apiData.predictions[req.session.user.id].map(
                (item, index) => ({
                    item_id: item.item_id,
                    score: item.score,
                    rank: item.rank || index + 1,
                }),
            );
        }

        // Return transformed data with both formats for compatibility
        res.json({
            ...apiData,
            recommendations: recommendations,
            count: recommendations.length,
        });
    } catch (error) {
        console.error("Error fetching recommendations:", error.message);
        res.status(500).json({
            error: "Failed to fetch recommendations",
            message: error.message,
            recommendations: [],
            fallback: [],
        });
    }
});

app.get("/api/user/actions", requireAuth, async (req, res) => {
    const actions = await readJSONFile(ACTIONS_FILE);
    const userActions = actions.filter((a) => a.userId === req.session.user.id);

    res.json(userActions);
});

app.get("/api/training/interactions", async (req, res) => {
    const actions = await readJSONFile(ACTIONS_FILE);

    const interactions = actions
        .filter((a) => a.action === "like" || a.action === "view")
        .map((a) => ({
            user_id: a.userId,
            item_id: a.productId.toString(),
            rating: a.action === "like" ? 5.0 : 1.0,
            timestamp: a.timestamp,
        }));

    res.json(interactions);
});

async function logUserAction(userId, productId, action) {
    const actions = await readJSONFile(ACTIONS_FILE);

    actions.push({
        userId,
        productId,
        action,
        timestamp: new Date().toISOString(),
    });

    await writeJSONFile(ACTIONS_FILE, actions);
}

app.use((req, res) => {
    res.status(404).send("Page not found");
});

async function startServer() {
    await ensureDataFiles();

    app.listen(PORT, () => {
        console.log(`Demo website running on http://localhost:${PORT}`);
        console.log(`API Server URL: ${API_SERVER_URL}`);
    });
}

startServer();
