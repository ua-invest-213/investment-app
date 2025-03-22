import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import bodyParser from 'body-parser';
import { Low } from 'lowdb';
import { JSONFile } from 'lowdb/node';
import bcrypt from 'bcryptjs';
import session from 'express-session';
import multer from 'multer';
import fs from 'fs';
import natural from 'natural';
import { createRequire } from 'module';
import { NlpManager } from 'node-nlp';
import nlp from 'compromise';
const require = createRequire(import.meta.url);

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const port = process.env.PORT || 3000;

const adapter = new JSONFile('db.json');

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

app.use(express.static(path.join(__dirname, 'public')));

const { GoogleGenerativeAI } = require("@google/generative-ai");
const genAI = new GoogleGenerativeAI("AIzaSyCu7_lNOEGQfPdY2kLcJXHXFB7we6kbeC0");
const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" });


app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', '/app/main/','home.html'));
});

app.listen(port, '0.0.0.0', () => {
    console.log(`Server running on port ${port}`);
  });
  