// Convert Bible JSON files to SQLite databases with FTS5 support
const fs = require('fs');
const path = require('path');
const Database = require('better-sqlite3');

const OLD_TESTAMENT_BOOKS = new Set([
  'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
  'Joshua', 'Judges', 'Ruth',
  '1 Samuel', '2 Samuel', '1 Kings', '2 Kings',
  '1 Chronicles', '2 Chronicles', 'Ezra', 'Nehemiah',
  'Tobit', 'Judith', 'Esther',
  'Job', 'Psalms', 'Proverbs', 'Ecclesiastes', 'Song of Solomon',
  'Wisdom', 'Sirach',
  'Isaiah', 'Jeremiah', 'Lamentations', 'Baruch', 'Ezekiel', 'Daniel',
  'Hosea', 'Joel', 'Amos', 'Obadiah', 'Jonah', 'Micah',
  'Nahum', 'Habakkuk', 'Zephaniah', 'Haggai', 'Zechariah', 'Malachi',
  '1 Maccabees', '2 Maccabees'
]);

const NEW_TESTAMENT_BOOKS = new Set([
  'Matthew', 'Mark', 'Luke', 'John',
  'Acts',
  'Romans', '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians',
  'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians',
  '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews',
  'James', '1 Peter', '2 Peter', '1 John', '2 John', '3 John', 'Jude',
  'Revelation'
]);

function isOldTestament(bookName) {
  return OLD_TESTAMENT_BOOKS.has(bookName);
}

function isNewTestament(bookName) {
  return NEW_TESTAMENT_BOOKS.has(bookName);
}

function createBibleDatabaseSchema(db) {
  db.exec(`CREATE TABLE IF NOT EXISTS verses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    translation TEXT NOT NULL,
    book TEXT NOT NULL,
    chapter INTEGER NOT NULL,
    verse INTEGER NOT NULL,
    text TEXT NOT NULL,
    identities TEXT,
    locations TEXT,
    cross_references TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(translation, book, chapter, verse)
  )`);
  
  db.exec(`CREATE INDEX IF NOT EXISTS idx_verses_book_chapter ON verses(book, chapter)`);
  db.exec(`CREATE INDEX IF NOT EXISTS idx_verses_translation ON verses(translation)`);

  db.exec(`CREATE VIRTUAL TABLE IF NOT EXISTS verses_fts USING fts5(
    translation,
    book,
    chapter,
    verse,
    text,
    identities,
    locations,
    cross_references,
    content='verses',
    content_rowid='id'
  )`);
  
  db.exec(`CREATE TRIGGER IF NOT EXISTS verses_fts_insert AFTER INSERT ON verses BEGIN
    INSERT INTO verses_fts(rowid, translation, book, chapter, verse, text, identities, locations, cross_references)
    VALUES (new.id, new.translation, new.book, new.chapter, new.verse, new.text, new.identities, new.locations, new.cross_references);
  END`);
  
  db.exec(`CREATE TRIGGER IF NOT EXISTS verses_fts_delete AFTER DELETE ON verses BEGIN
    INSERT INTO verses_fts(verses_fts, rowid, translation, book, chapter, verse, text, identities, locations, cross_references)
    VALUES ('delete', old.id, old.translation, old.book, old.chapter, old.verse, old.text, old.identities, old.locations, old.cross_references);
  END`);
  
  db.exec(`CREATE TRIGGER IF NOT EXISTS verses_fts_update AFTER UPDATE ON verses BEGIN
    INSERT INTO verses_fts(verses_fts, rowid, translation, book, chapter, verse, text, identities, locations, cross_references)
    VALUES ('delete', old.id, old.translation, old.book, old.chapter, old.verse, old.text, old.identities, old.locations, old.cross_references);
    INSERT INTO verses_fts(rowid, translation, book, chapter, verse, text, identities, locations, cross_references)
    VALUES (new.id, new.translation, new.book, new.chapter, new.verse, new.text, new.identities, new.locations, new.cross_references);
  END`);
}

function createCatechismDatabaseSchema(db) {
  db.exec(`CREATE TABLE IF NOT EXISTS paragraphs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section_id TEXT NOT NULL,
    paragraph_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    identities TEXT,
    locations TEXT,
    cross_references TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(section_id, paragraph_index)
  )`);
  
  db.exec(`CREATE INDEX IF NOT EXISTS idx_paragraphs_section ON paragraphs(section_id)`);

  db.exec(`CREATE VIRTUAL TABLE IF NOT EXISTS paragraphs_fts USING fts5(
    section_id,
    paragraph_index,
    text,
    identities,
    locations,
    cross_references,
    content='paragraphs',
    content_rowid='id'
  )`);
  
  db.exec(`CREATE TRIGGER IF NOT EXISTS paragraphs_fts_insert AFTER INSERT ON paragraphs BEGIN
    INSERT INTO paragraphs_fts(rowid, section_id, paragraph_index, text, identities, locations, cross_references)
    VALUES (new.id, new.section_id, new.paragraph_index, new.text, new.identities, new.locations, new.cross_references);
  END`);
  
  db.exec(`CREATE TRIGGER IF NOT EXISTS paragraphs_fts_delete AFTER DELETE ON paragraphs BEGIN
    INSERT INTO paragraphs_fts(paragraphs_fts, rowid, section_id, paragraph_index, text, identities, locations, cross_references)
    VALUES ('delete', old.id, old.section_id, old.paragraph_index, old.text, old.identities, old.locations, old.cross_references);
  END`);
  
  db.exec(`CREATE TRIGGER IF NOT EXISTS paragraphs_fts_update AFTER UPDATE ON paragraphs BEGIN
    INSERT INTO paragraphs_fts(paragraphs_fts, rowid, section_id, paragraph_index, text, identities, locations, cross_references)
    VALUES ('delete', old.id, old.section_id, old.paragraph_index, old.text, old.identities, old.locations, old.cross_references);
    INSERT INTO paragraphs_fts(rowid, section_id, paragraph_index, text, identities, locations, cross_references)
    VALUES (new.id, new.section_id, new.paragraph_index, new.text, new.identities, new.locations, new.cross_references);
  END`);
}

function extractTextFromParagraph(paragraph) {
  if (!paragraph.elements) return '';
  
  return paragraph.elements
    .map(element => {
      if (element.type === 'text') {
        return element.text || '';
      } else if (element.type === 'ref') {
        return `[${element.number || ''}]`;
      }
      return '';
    })
    .join('')
    .trim();
}

function importBibleJson(db, jsonPath, translationName, filterBooks = null) {
  const data = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
  const insertStmt = db.prepare(`INSERT OR REPLACE INTO verses (translation, book, chapter, verse, text, identities, locations, cross_references)
    VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL)`);
  
  const insertMany = db.transaction((verses) => {
    for (const verse of verses) {
      insertStmt.run(translationName, verse.book, verse.chapter, verse.verse, verse.text);
    }
  });

  const verses = [];
  let bookCount = 0;
  let verseCount = 0;

  for (const [bookName, chapters] of Object.entries(data)) {
    if (bookName === 'charset') continue;
    if (filterBooks && !filterBooks(bookName)) continue;

    for (const [chapterNum, versesObj] of Object.entries(chapters)) {
      const chapter = parseInt(chapterNum, 10);
      if (isNaN(chapter)) continue;

      for (const [verseNum, text] of Object.entries(versesObj)) {
        const verse = parseInt(verseNum, 10);
        if (isNaN(verse)) continue;

        verses.push({
          book: bookName,
          chapter: chapter,
          verse: verse,
          text: String(text).trim()
        });
        verseCount++;
      }
    }
    bookCount++;
  }

  console.log(`  Processing ${bookCount} books, ${verseCount} verses...`);
  
  const batchSize = 1000;
  for (let i = 0; i < verses.length; i += batchSize) {
    const batch = verses.slice(i, i + batchSize);
    insertMany(batch);
  }

  console.log(`  ✓ Imported ${verseCount} verses from ${translationName}`);
}

function importCatechismJson(db, jsonPath) {
  const data = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
  const pageNodes = data.page_nodes || {};
  const insertStmt = db.prepare(`INSERT OR REPLACE INTO paragraphs (section_id, paragraph_index, text, identities, locations, cross_references)
    VALUES (?, ?, ?, NULL, NULL, NULL)`);
  
  const insertMany = db.transaction((paragraphs) => {
    for (const para of paragraphs) {
      insertStmt.run(para.section_id, para.paragraph_index, para.text);
    }
  });

  const paragraphs = [];
  let sectionCount = 0;
  let paragraphCount = 0;

  for (const [sectionId, sectionData] of Object.entries(pageNodes)) {
    if (!sectionData.paragraphs || !Array.isArray(sectionData.paragraphs)) continue;
    
    sectionData.paragraphs.forEach((paragraph, index) => {
      const text = extractTextFromParagraph(paragraph);
      if (text) {
        paragraphs.push({
          section_id: sectionId,
          paragraph_index: index,
          text: text
        });
        paragraphCount++;
      }
    });
    sectionCount++;
  }

  console.log(`  Processing ${sectionCount} sections, ${paragraphCount} paragraphs...`);
  
  const batchSize = 1000;
  for (let i = 0; i < paragraphs.length; i += batchSize) {
    const batch = paragraphs.slice(i, i + batchSize);
    insertMany(batch);
  }

  console.log(`  ✓ Imported ${paragraphCount} paragraphs from Catechism`);
}

function main() {
  const rootDir = path.dirname(__dirname);
  const outputDir = path.join(rootDir, 'databases');
  
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // Find Bible files
  const bibleFiles = [];
  const files = fs.readdirSync(rootDir);
  for (const file of files) {
    if (file.endsWith('.json') && file !== 'package.json' && file !== 'package-lock.json' && file !== 'ccc.json') {
      const filePath = path.join(rootDir, file);
      try {
        const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
        if (data.Genesis || data['1 Samuel'] || data.Matthew) {
          const name = path.basename(file, '.json').toLowerCase();
          bibleFiles.push({ path: filePath, name: name });
        }
      } catch (e) {
        // Skip invalid JSON files
      }
    }
  }
  
  if (bibleFiles.length === 0) {
    console.error('No Bible JSON files found!');
    process.exit(1);
  }
  
  console.log(`Found ${bibleFiles.length} Bible translation(s): ${bibleFiles.map(f => f.name.toUpperCase()).join(', ')}`);

  // Create 6 mobile databases + 1 combined database
  console.log('\nCreating mobile databases (7 databases)...');
  
  const mobileDbs = {
    'bible_cpdv_old_testament.db': { translation: 'cpdv', filter: isOldTestament },
    'bible_cpdv_new_testament.db': { translation: 'cpdv', filter: isNewTestament },
    'bible_drb_old_testament.db': { translation: 'drb', filter: isOldTestament },
    'bible_drb_new_testament.db': { translation: 'drb', filter: isNewTestament },
    'bible_cpdv.db': { translation: 'cpdv', filter: null },
    'bible_drb.db': { translation: 'drb', filter: null },
    'bibles.db': { translation: 'both', filter: null }
  };

  const dbInstances = {};
  for (const [dbName, config] of Object.entries(mobileDbs)) {
    const dbPath = path.join(outputDir, dbName);
    dbInstances[dbName] = new Database(dbPath);
    createBibleDatabaseSchema(dbInstances[dbName]);
    console.log(`Created ${dbName}`);
  }

  // Import Bible data
  for (const { path: jsonPath, name: translationName } of bibleFiles) {
    if (!fs.existsSync(jsonPath)) {
      console.warn(`Warning: ${jsonPath} not found, skipping...`);
      continue;
    }

    console.log(`\nImporting ${translationName.toUpperCase()}...`);

    for (const [dbName, config] of Object.entries(mobileDbs)) {
      if (config.translation === translationName || config.translation === 'both') {
        const filterDesc = config.filter === isOldTestament ? 'Old Testament' :
                          config.filter === isNewTestament ? 'New Testament' : 'Complete';
        console.log(`  → ${dbName} (${filterDesc})`);
        importBibleJson(dbInstances[dbName], jsonPath, translationName.toUpperCase(), config.filter);
      }
    }
  }

  // Optimize and close Bible databases
  console.log('\nOptimizing Bible databases...');
  for (const [dbName, db] of Object.entries(dbInstances)) {
    db.exec('VACUUM; ANALYZE;');
    db.close();
  }

  // Create Catechism database
  const cccPath = path.join(rootDir, 'ccc.json');
  if (fs.existsSync(cccPath)) {
    console.log('\nCreating Catechism database...');
    const cccDb = new Database(path.join(outputDir, 'catechism.db'));
    createCatechismDatabaseSchema(cccDb);
    console.log('Created catechism.db');
    
    console.log('\nImporting Catechism...');
    importCatechismJson(cccDb, cccPath);
    
    console.log('\nOptimizing Catechism database...');
    cccDb.exec('VACUUM; ANALYZE;');
    cccDb.close();
  } else {
    console.log('\nWarning: ccc.json not found, skipping Catechism database');
  }

  console.log('\n✓ Conversion complete!');
  console.log(`\nBible databases (7 databases):`);
  for (const dbName of Object.keys(mobileDbs)) {
    console.log(`  - ${path.join(outputDir, dbName)}`);
  }
  if (fs.existsSync(cccPath)) {
    console.log(`\nCatechism database:`);
    console.log(`  - ${path.join(outputDir, 'catechism.db')}`);
  }
  console.log(`\nAll databases include:`);
  console.log(`  - FTS5 full-text search support`);
  console.log(`  - Metadata fields: identities, locations, cross_references`);
}

if (require.main === module) {
  main();
}

module.exports = { main, createBibleDatabaseSchema, createCatechismDatabaseSchema, importBibleJson, importCatechismJson };
