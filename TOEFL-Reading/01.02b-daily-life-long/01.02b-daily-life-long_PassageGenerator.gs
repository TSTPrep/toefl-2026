// TOEFL 2026 - Reading Section - Daily Life LONG - Passage Generator
// This script generates long passages and questions for TOEFL practice exercises.

// Function to load configuration from the 'Config' sheet
function loadConfig() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  // Find the sheet by its GID - **NOTE: This will need to be updated to the new sheet's GID**
  const configSheet = ss.getSheets().filter(sheet => sheet.getSheetName() == 'Config')[0]; 
  
  if (!configSheet) {
    Logger.log("Error: Configuration sheet named 'Config' not found. Please create a 'Config' sheet.");
    return {};
  }

  const data = configSheet.getDataRange().getValues();
  const config = {};
  // Start from the second row to skip header
  for (let i = 1; i < data.length; i++) {
    const key = data[i][0];
    let value = data[i][1];
    if (key) {
      config[key] = value;
    }
  }

  // Explicitly load Main Prompt from cell B16
  const mainPrompt = configSheet.getRange('B16').getValue();
  if (mainPrompt) {
    config['Main Prompt'] = mainPrompt;
  }
  
  return config;
}

// Function to apply default values and handle key variations
function applyDefaultsToConfig(config) {
  const defaults = {
    'MODEL': 'gpt-5-mini',
    'TEMPERATURE': 1,
    'MAX_COMPLETION_TOKENS': 8000,
    'API_KEY': '', // Placeholder, user must provide
    'OPENAI_URL': 'https://api.openai.com/v1/chat/completions',
    'Passage Word Count Min': 130,
    'Passage Word Count Max': 170,
    'Genre Distribution Announcements': 0.1,
    'Genre Distribution Emails': 0.9,
    'Gist Purpose Question %': 0.55, // 50-60%
    'Gist Content Question %': 0, // Omitted
    'Factual Info Question %': 0.9, // 90% at least one, 40-50% two
    'Negative Factual Info Question %': 0.1, // 10% at most one
    'Inference Question %': 0.65, // 60-70%
    'TARGET_SHEET_GID': '', // Placeholder, user must provide the GID of the target sheet
    'Main Prompt': 'You are an expert in creating educational content for TOEFL Reading questions. Your task is to generate a long passage and five multiple-choice questions based on a given topic and instructions.\\n- The passage must be between 130 and 170 words.\\n- The passage must be in the style of a "Daily Life" text, such as an email or announcement, with a formal-but-simple register appropriate for a CEFR B1-B2 level.\\n- Use short, direct sentences and everyday vocabulary. Avoid idioms or culturally specific slang.\\n- The passage must include a date or time, a specific requirement or condition (e.g., "bring ID," "RSVP by Friday"), and subtle clues that can be used for inference questions.\\n- The questions should test comprehension of the passage.\\n- Avoid using "for example" explicitly; just give examples.\\n- Avoid big lists in both intact sentences and sentences with missing letters.\\n- If applicable, split missing letters across two sentences. The first sentence can have most, and the second can have missing letters only at the beginning.\\n- Ensure there are two complete sentences at the end after any missing letter sections.\\n- Do not always use an obvious “xxx is yyy” opening.\\n- Avoid overly technical vocabulary. Aim for freshman-level university textbook language that a newcomer would understand. The trickiest word in ETS samples was "cognitive."\\n- The second and third sentences should ideally not use proper nouns.\\n- Avoid long-winded final sentences.\\n- Ensure sentences with missing letters do not contain lists, as this makes it too difficult for students.\\n- Introduce more variety in sentence structure beyond the opening sentence.\\n\\nGenerate a long {genre} about "{topic}". It must be between 130 and 170 words. Then, generate five multiple-choice questions. Each question must have one correct answer and three plausible distractors.\\n\\nYou must output your response in a JSON format that adheres to the provided schema.',
    'JSON Output Schema': `
{
  "passage": "string",
  "question1": {
    "question": "string",
    "answer": "string",
    "distractors": ["string", "string", "string"]
  },
  "question2": {
    "question": "string",
    "answer": "string",
    "distractors": ["string", "string", "string"]
  },
  "question3": {
    "question": "string",
    "answer": "string",
    "distractors": ["string", "string", "string"]
  },
  "question4": {
    "question": "string",
    "answer": "string",
    "distractors": ["string", "string", "string"]
  },
  "question5": {
    "question": "string",
    "answer": "string",
    "distractors": ["string", "string", "string"]
  }
}
`
  };

  // Merge config with defaults, prioritizing config values
  const mergedConfig = { ...defaults, ...config };

  // Handle specific key aliases/transformations
  if (mergedConfig['Model']) {
    mergedConfig['MODEL'] = mergedConfig['Model'];
    delete mergedConfig['Model'];
  }
  if (mergedConfig['Temperature']) {
    mergedConfig['TEMPERATURE'] = mergedConfig['Temperature'];
    delete mergedConfig['Temperature'];
  }
  if (mergedConfig['Max Output Tokens']) {
    mergedConfig['MAX_COMPLETION_TOKENS'] = mergedConfig['Max Output Tokens'];
    delete mergedConfig['Max Output Tokens'];
  }

  // Reconstruct the nested PASSAGE_LENGTH object from flat keys
  mergedConfig.PASSAGE_LENGTH = {
    MIN: mergedConfig['Passage Word Count Min'],
    MAX: mergedConfig['Passage Word Count Max']
  };

  return mergedConfig;
}

// Load configuration at runtime
const CONFIG = applyDefaultsToConfig(loadConfig());

// Function to load topics from the 'Topics' sheet
function loadTopics() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  // Find the sheet by its GID - **NOTE: This will need to be updated to the new sheet's GID**
  const topicsSheet = ss.getSheets().filter(sheet => sheet.getSheetName() == 'Topics')[0]; 

  if (!topicsSheet) {
    Logger.log("Error: Topics sheet named 'Topics' not found. Please create a 'Topics' sheet.");
    return {};
  }

  const data = topicsSheet.getDataRange().getValues();
  const topics = {};
  let currentCategory = "";

  // Start from the second row to skip the header
  for (let i = 1; i < data.length; i++) {
    const category = data[i][0] || currentCategory;
    const topic = data[i][1];
    
    if (topic) {
      if (!topics[category]) {
        topics[category] = [];
      }
      topics[category].push(topic);
      currentCategory = category;
    }
  }
  return topics;
}

// Load topics at runtime
const TOPICS = loadTopics();

// Main function to generate a passage and questions
function generateDailyLifeLongPassage(topic, outputRow) {
  const sheet = getSheetByGid(CONFIG['TARGET_SHEET_GID']);
  if (!sheet) {
    Logger.log("Error: Target sheet with GID " + CONFIG['TARGET_SHEET_GID'] + " not found.");
    return;
  }
  Logger.log("Generating passage for topic: " + topic);

  const genre = Math.random() < CONFIG['Genre Distribution Emails'] ? 'email with subject line, greeting and sign-off in this format:\\nSubject: <Subject Line>\\n<e-mail body>'
  : 'announcement/notice format';

  const generatedContent = generatePassageWithAI(topic, genre);
  if (!generatedContent) {
    sheet.getRange(outputRow, 2).setValue("Error: Failed to generate content");
    return;
  }

  // Assuming the AI returns content in a structured format, e.g., JSON string
  try {
    const content = JSON.parse(generatedContent);
    sheet.getRange(outputRow, 1).setValue(topic);
    sheet.getRange(outputRow, 2).setValue(content.passage || "[Missing Passage]");

    if (content.question1) {
      sheet.getRange(outputRow, 3).setValue(content.question1.question || "[Missing Question 1]");
      sheet.getRange(outputRow, 4).setValue(content.question1.answer || "[Missing Answer 1]");
      sheet.getRange(outputRow, 5, 1, 3).setValues([content.question1.distractors || ["[Missing]", "[Missing]", "[Missing]"]]);
    } else {
      sheet.getRange(outputRow, 3).setValue("[Missing Question 1]");
    }

    if (content.question2) {
      sheet.getRange(outputRow, 8).setValue(content.question2.question || "[Missing Question 2]");
      sheet.getRange(outputRow, 9).setValue(content.question2.answer || "[Missing Answer 2]");
      sheet.getRange(outputRow, 10, 1, 3).setValues([content.question2.distractors || ["[Missing]", "[Missing]", "[Missing]"]]);
    } else {
      sheet.getRange(outputRow, 8).setValue("[Missing Question 2]");
    }

    if (content.question3) {
      sheet.getRange(outputRow, 13).setValue(content.question3.question || "[Missing Question 3]");
      sheet.getRange(outputRow, 14).setValue(content.question3.answer || "[Missing Answer 3]");
      sheet.getRange(outputRow, 15, 1, 3).setValues([content.question3.distractors || ["[Missing]", "[Missing]", "[Missing]"]]);
    } else {
      sheet.getRange(outputRow, 13).setValue("[Missing Question 3]");
    }

    if (content.question4) {
      sheet.getRange(outputRow, 18).setValue(content.question4.question || "[Missing Question 4]");
      sheet.getRange(outputRow, 19).setValue(content.question4.answer || "[Missing Answer 4]");
      sheet.getRange(outputRow, 20, 1, 3).setValues([content.question4.distractors || ["[Missing]", "[Missing]", "[Missing]"]]);
    } else {
      sheet.getRange(outputRow, 18).setValue("[Missing Question 4]");
    }

    if (content.question5) {
      sheet.getRange(outputRow, 23).setValue(content.question5.question || "[Missing Question 5]");
      sheet.getRange(outputRow, 24).setValue(content.question5.answer || "[Missing Answer 5]");
      sheet.getRange(outputRow, 25, 1, 3).setValues([content.question5.distractors || ["[Missing]", "[Missing]", "[Missing]"]]);
    } else {
      sheet.getRange(outputRow, 23).setValue("[Missing Question 5]");
    }

  } catch (e) {
    Logger.log("Error parsing AI response: " + e.toString());
    sheet.getRange(outputRow, 2).setValue("Error: Could not parse AI response.");
  }

  Logger.log("Passage generation completed for row " + outputRow);
}

// Generate passage using gpt-5-mini
function generatePassageWithAI(topic, genre) {
  const prompt = buildPrompt(topic, genre);

  const payload = {
    model: CONFIG['MODEL'],
    messages: [
      {
        role: "user",
        content: prompt + "\n\nHere is the JSON schema to follow:\n" + CONFIG['JSON Output Schema']
      }
    ],
    temperature: CONFIG['TEMPERATURE'],
    max_completion_tokens: CONFIG['MAX_COMPLETION_TOKENS']
  };

  Logger.log("Complete prompt sent to API: " + payload.messages[0].content);

  try {
    const response = UrlFetchApp.fetch(CONFIG['OPENAI_URL'], {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + CONFIG['API_KEY']
      },
      payload: JSON.stringify(payload),
      muteHttpExceptions: true // Add this to get full error response
    });

    const responseText = response.getContentText();
    Logger.log("Raw API Response: " + responseText);

    const data = JSON.parse(responseText);

    if (data.error) {
      Logger.log("API Error: " + data.error.message);
      return null;
    }

    if (data.choices && data.choices.length > 0 && data.choices[0].message) {
      return data.choices[0].message.content.trim();
    } else {
      Logger.log("Unexpected API response structure: " + responseText);
      return null;
    }

  } catch (error) {
    Logger.log("Error generating passage: " + error.toString());
    return null;
  }
}

// Build the detailed prompt for passage generation
function buildPrompt(topic, genre) {
  let prompt = CONFIG['Main Prompt'] || ''; // Fallback to empty string
  
  // Log before replacement
  Logger.log("Before replacement - topic: " + topic + ", genre: " + genre);
  Logger.log("Prompt contains {topic}: " + prompt.includes('{topic}'));
  Logger.log("Prompt contains {genre}: " + prompt.includes('{genre}'));
  
  // Replace placeholders
  prompt = prompt.replace(/{topic}/g, topic);
  prompt = prompt.replace(/{genre}/g, genre);
  
  // Log after replacement
  Logger.log("After replacement - still contains {topic}: " + prompt.includes('{topic}'));
  Logger.log("After replacement - still contains {genre}: " + prompt.includes('{genre}'));
  
  return prompt;
}

// Utility function
function countWords(text) {
  return text.trim().split(/\s+/).length;
}

// --- Trigger-Based Batch Processing ---

// Starts the batch generation process by setting up a time-driven trigger.
function startBatchProcess() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const batchSize = sheet.getRange('B1').getValue() || 5;
  
  // Clear any existing triggers to prevent duplicates
  stopBatchProcess(); 
  
  // Use PropertiesService to store the state
  const userProperties = PropertiesService.getUserProperties();
  userProperties.setProperty('batchIndex', '0');
  userProperties.setProperty('batchSize', batchSize.toString());
  
  // Create a trigger to run the processing function every 1 minute
  ScriptApp.newTrigger('processBatchChunk')
      .timeBased()
      .everyMinutes(1)
      .create();
      
  SpreadsheetApp.getUi().alert('Batch process started. Chunks of up to 10 passages will be generated in the background every minute. You can close this sheet.');
}

// Processes a chunk of up to 10 items from the batch. This function is run by the trigger.
function processBatchChunk() {
  const userProperties = PropertiesService.getUserProperties();
  let index = parseInt(userProperties.getProperty('batchIndex'), 10);
  const size = parseInt(userProperties.getProperty('batchSize'), 10);
  const chunkSize = 10; // Process up to 10 passages per run

  for (let i = 0; i < chunkSize && index < size; i++) {
    // Generate one passage
    generateSinglePassage();
    
    // Update the index for the next run
    index++;
    userProperties.setProperty('batchIndex', index.toString());
  }
  
  if (index >= size) {
    // Batch is complete, so stop the process
    stopBatchProcess();
    Logger.log('Batch process completed and trigger has been removed.');
  }
}

// Stops the batch process by deleting the trigger and clearing properties.
function stopBatchProcess() {
  // Delete all triggers for this script
  const triggers = ScriptApp.getProjectTriggers();
  for (let i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === 'processBatchChunk') {
      ScriptApp.deleteTrigger(triggers[i]);
    }
  }
  
  // Clear the stored properties
  const userProperties = PropertiesService.getUserProperties();
  userProperties.deleteProperty('batchIndex');
  userProperties.deleteProperty('batchSize');
}


// Wrapper function for single random passage generation from menu
function generateSinglePassage() {
  const sheet = getSheetByGid(CONFIG['TARGET_SHEET_GID']);
  if (!sheet) {
    SpreadsheetApp.getUi().alert("Error: Target sheet with GID " + CONFIG['TARGET_SHEET_GID'] + " not found. Please check your configuration.");
    return;
  }
  const startRow = sheet.getRange('C1').getValue() || 5;
  const nextEmptyRow = Math.max(startRow, sheet.getLastRow() + 1);
  const topic = getTopicFromSheet();
  generateDailyLifeLongPassage(topic, nextEmptyRow);
}

// Get topic based on sheet configuration
function getTopicFromSheet() {
  const sheet = getSheetByGid(CONFIG['TARGET_SHEET_GID']);
  if (!sheet) {
    Logger.log("Error: Target sheet with GID " + CONFIG['TARGET_SHEET_GID'] + " not found. Cannot get topic.");
    return "Default Topic";
  }
  const mode = sheet.getRange('A1').getValue();
  const category = sheet.getRange('A2').getValue();
  const specificTopic = sheet.getRange('A3').getValue();

  if (mode === "Specific Topic" && specificTopic) {
    return specificTopic;
  }

  if (mode === "Category Random" && category && TOPICS[category]) {
    const categoryTopics = TOPICS[category];
    return categoryTopics[Math.floor(Math.random() * categoryTopics.length)];
  }

  // Default to "All Random"
  const allTopics = Object.values(TOPICS).flat();
  return allTopics[Math.floor(Math.random() * allTopics.length)];
}

// Menu function to add custom menu items
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('TOEFL Daily Life LONG')
    .addItem('Generate Single Passage', 'generateSinglePassage')
    .addSeparator()
    .addItem('Start Batch Process', 'startBatchProcess')
    .addItem('Stop Batch Process', 'stopBatchProcess')
    .addSeparator()
    .addItem('Start Edit Sheet Conversions', 'startEditSheetConversions')
    .addItem('Delete Editing Sheets', 'deleteEditingSheets') // New menu item
    .addToUi();
}

// Helper function to get a sheet by its GID
function getSheetByGid(gid) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const allSheets = ss.getSheets();
  for (let i = 0; i < allSheets.length; i++) {
    if (allSheets[i].getSheetId() == gid) {
      return allSheets[i];
    }
  }
  return null; // Return null if no sheet with the given GID is found
}

/**
 * Duplicates the 'Template' sheet, populates it with data, and creates a hyperlink
 * back to the new sheet in the 'Generated Passages' sheet.
 * If a sheet for a specific row already exists, it is deleted and recreated.
 */
function startEditSheetConversions() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const generateSheet = ss.getSheetByName("Generated Passages");
  const templateSheet = ss.getSheetByName("Template");

  if (!generateSheet) {
    SpreadsheetApp.getUi().alert('Error: "Generated Passages" sheet not found.');
    return;
  }
  if (!templateSheet) {
    SpreadsheetApp.getUi().alert('Error: "Template" sheet not found.');
    return;
  }

  const startRow = generateSheet.getRange('C1').getValue();
  const numRows = generateSheet.getRange('B1').getValue();

  if (!startRow || !numRows || typeof startRow !== 'number' || typeof numRows !== 'number' || startRow <= 1 || numRows <= 0) {
    SpreadsheetApp.getUi().alert('Please enter a valid start row (greater than 1) in C1 and a valid number of rows in B1.');
    return;
  }

  const spreadsheetUrl = ss.getUrl();

  for (let i = 0; i < numRows; i++) {
    const currentRow = startRow + i;
    const newSheetName = "Row " + currentRow;

    const existingSheet = ss.getSheetByName(newSheetName);
    if (existingSheet) {
      ss.deleteSheet(existingSheet);
      Logger.log(`Deleted existing sheet: "${newSheetName}"`);
    }

    const newSheet = templateSheet.copyTo(ss);
    newSheet.setName(newSheetName);
    ss.setActiveSheet(newSheet);

    const sourceData = generateSheet.getRange(currentRow, 1, 1, 27).getValues()[0];
    const topicText = sourceData[0];

    // --- NEW FEATURE: Create Hyperlink ---
    const sheetUrl = '#gid=' + newSheet.getSheetId();
    const linkCell = generateSheet.getRange(currentRow, 1);
    const richTextLink = SpreadsheetApp.newRichTextValue()
      .setText(topicText)
      .setLinkUrl(sheetUrl)
      .build();
    linkCell.setRichTextValue(richTextLink);
    // --- END NEW FEATURE ---


    // --- Populate the new sheet ---
    // Note: We use topicText here instead of sourceData[0] for clarity.
    newSheet.getRange('B3').setValue(topicText);       // Column A -> B3 (Topic)
    newSheet.getRange('B6').setValue(sourceData[1]);   // Column B -> B6 (Passage)
    newSheet.getRange('B9').setValue(sourceData[2]);   // Column C -> B9 (Q1 Question)
    newSheet.getRange('B12').setValue(sourceData[3]);  // Column D -> B12 (Q1 Answer)
    newSheet.getRange('B15:B17').setValues(sourceData.slice(4, 7).map(x => [x])); // E,F,G -> B15:B17

    // --- Question 2 ---
    newSheet.getRange('B20').setValue(sourceData[7]);  // Column H -> B20 (Q2 Question)
    newSheet.getRange('B23').setValue(sourceData[8]);  // Column I -> B23 (Q2 Answer)
    newSheet.getRange('B26:B28').setValues(sourceData.slice(9, 12).map(x => [x])); // J,K,L -> B26:B28

    // --- Question 3 ---
    newSheet.getRange('B31').setValue(sourceData[12]); // Column M -> B31 (Q3 Question)
    newSheet.getRange('B34').setValue(sourceData[13]); // Column N -> B34 (Q3 Answer)
    newSheet.getRange('B37:B39').setValues(sourceData.slice(14, 17).map(x => [x])); // O,P,Q -> B37:B39

    // --- Question 4 ---
    newSheet.getRange('B42').setValue(sourceData[17]); // Column R -> B42 (Q4 Question)
    newSheet.getRange('B45').setValue(sourceData[18]); // Column S -> B45 (Q4 Answer)
    newSheet.getRange('B48:B50').setValues(sourceData.slice(19, 22).map(x => [x])); // T,U,V -> B48:B50

    // --- Question 5 ---
    newSheet.getRange('B53').setValue(sourceData[22]); // Column W -> B53 (Q5 Question)
    newSheet.getRange('B56').setValue(sourceData[23]); // Column X -> B56 (Q5 Answer)
    newSheet.getRange('B59:B61').setValues(sourceData.slice(24, 27).map(x => [x])); // Y,Z,AA -> B59:B61

    Logger.log(`Successfully created and populated sheet: "${newSheetName}" and added link.`);
  }
  SpreadsheetApp.getUi().alert('Sheet conversion process completed!');
}

/**
 * Deletes a range of sheets and removes the corresponding hyperlinks and text formatting
 * in column A of the 'Generated Passages' sheet. The process is based on the start row
 * and number of rows specified in cells C1 and B1.
 */
function deleteEditingSheets() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const generateSheet = ss.getSheetByName("Generated Passages");

  if (!generateSheet) {
    SpreadsheetApp.getUi().alert('Error: "Generated Passages" sheet not found.');
    return;
  }

  // Read the start row from C1 and the amount of rows from B1.
  const startRow = generateSheet.getRange('C1').getValue();
  const numRows = generateSheet.getRange('B1').getValue();

  if (!startRow || !numRows || typeof startRow !== 'number' || typeof numRows !== 'number' || startRow <= 1 || numRows <= 0) {
    SpreadsheetApp.getUi().alert('Please enter a valid start row (greater than 1) in C1 and a valid number of rows in B1.');
    return;
  }

  let deletedCount = 0;
  // Loop through the specified rows to identify sheets and links for deletion.
  for (let i = 0; i < numRows; i++) {
    const currentRow = startRow + i;
    const sheetName = "Row " + currentRow;
    const sheetToDelete = ss.getSheetByName(sheetName);

    // --- FIX: Remove Hyperlink and Clear Formatting ---
    const linkCell = generateSheet.getRange(currentRow, 1);
    const topicText = linkCell.getValue(); // Get the plain text

    // Set the value back to plain text and then clear all formatting.
    // This removes the blue color and underline.
    linkCell.setValue(topicText).clearFormat();
    // --- END FIX ---

    // If the sheet exists, delete it.
    if (sheetToDelete) {
      ss.deleteSheet(sheetToDelete);
      Logger.log(`Deleted sheet: "${sheetName}" and reset its link cell.`);
      deletedCount++;
    } else {
      Logger.log(`Sheet "${sheetName}" not found. Skipping link cell reset.`);
    }
  }

  SpreadsheetApp.getUi().alert(`Deletion process completed. ${deletedCount} sheets were removed and their links were cleared.`);
}