const express = require("express");
const cors = require("cors");
const fs = require("fs");
const path = require("path");

const app = express();
const PORT = process.env.PORT || 3000;
const DATA_FILE = path.join(__dirname, "data.json");

app.use(cors());
app.use(express.json());

// Healthcheck
app.get("/api", (req, res) => {
  res.json({ ok: true, message: "API funcionando correctamente ✅" });
});

// Devuelve todo el catálogo
app.get("/api/videos", (req, res) => {
  try {
    const raw = fs.readFileSync(DATA_FILE, "utf8");
    const parsed = JSON.parse(raw);
    res.json(parsed);
  } catch (err) {
    console.error("Error leyendo data.json:", err.message);
    res.status(500).json({ error: "No se pudo leer data.json en el backend" });
  }
});

// Devuelve solo una categoría
app.get("/api/videos/by-category/:cat", (req, res) => {
  try {
    const raw = fs.readFileSync(DATA_FILE, "utf8");
    const parsed = JSON.parse(raw);

    const catKey = decodeURIComponent(req.params.cat);
    const list = parsed[catKey];

    if (!list) {
      return res.status(404).json({ error: "Categoría no encontrada" });
    }

    res.json(list);
  } catch (err) {
    console.error("Error leyendo data.json:", err.message);
    res.status(500).json({ error: "No se pudo leer data.json en el backend" });
  }
});

// Iniciar servidor
app.listen(PORT, () => {
  console.log(`Servidor backend escuchando en http://localhost:${PORT}`);
});
