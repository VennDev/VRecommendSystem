const express = require("express");
const session = require("express-session");
const bodyParser = require("body-parser");
const cookieParser = require("cookie-parser");
const axios = require("axios");
const fs = require("fs").promises;
const path = require("path");
const productsData = require("./products_data");

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
            await fs.writeFile(
                PRODUCTS_FILE,
                JSON.stringify(productsData, null, 2),
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
