// TOEFL 2026 - Reading Section - Academic Passages - Passage Generator
// This script generates academic passages and questions for TOEFL practice exercises.

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
    'Passage Word Count Min': 165,
    'Passage Word Count Max': 210,
    // Genre Distribution not applicable for academic passages, removed or set to 0
    'Gist Content Question %': 0.125, // 10-15%
    'Factual Info Question %': 0.95, // 95% of the time 1-2 questions
    'Negative Factual Info Question %': 0.45, // 40-50%
    'Inference Question %': 0.675, // 60-75%
    'Vocabulary Question %': 0.8, // 80% first question, 5% zero
    'Organization Question %': 0.2, // 20%
    'Author\'s Purpose Question %': 0.9, // 90% frequency, 5-10% two
    'Insert Text Question %': 0.15, // 15%
    'Click on the Sentence %': 0.15, // 15%
    'TARGET_SHEET_GID': '', // Placeholder, user must provide the GID of the target sheet
    'System Prompt': 'You are an expert in creating educational content for TOEFL Reading questions. Your task is to generate an academic passage and five multiple-choice questions based on a given topic and instructions.\n- Background knowledge is not required to understand the passage.\n- The passage must be between 165 and 210 words long, structured into 2-4 paragraphs.\n- Each passage must have a clear structure: introduction → explanation → examples → broader implications or conclusion.\n- The passage must be written in a neutral, academic tone — similar to a university-level textbook or lecture, but simplified for ESL learners.\n- Sentences are moderately complex but not overly dense; technical terms are introduced with short explanations.\n- Avoid personal opinions; instead, present facts, research findings, or historical accounts.\n- The opening paragraph should introduce the topic in a straightforward way.\n- Middle paragraphs should provide evidence, examples, case studies, or contrasting perspectives.\n- The final paragraph should often widen the lens — talking about significance, implications, or ongoing research.\n- When creating passages, imagine writing a short, engaging, entry-level textbook section on a topic a curious college freshman might encounter for the first time. It should be fact-based, accessible, structured, and balanced with both examples and implications.\n- The questions should test comprehension of the passage.\n- Avoid using "for example" explicitly; just give examples.\n- Avoid big lists in both intact sentences and sentences with missing letters.\n- If applicable, split missing letters across two sentences. The first sentence can have most, and the second can have missing letters only at the beginning.\n- Ensure there are two complete sentences at the end after any missing letter sections.\n- Do not always use an obvious “xxx is yyy” opening.\n- Avoid overly technical vocabulary. Aim for freshman-level university textbook language that a newcomer would understand. The trickiest word in ETS samples was "cognitive."\n- The second and third sentences should ideally not use proper nouns.\n- Avoid long-winded final sentences.\n- Ensure sentences with missing letters do not contain lists, as this makes it too difficult for students.\n- Introduce more variety in sentence structure beyond the opening sentence.\n- You must output your response in a JSON format that adheres to the provided schema.',
    'User Prompt Template': 'Generate an academic passage about "{topic}". It must be between 165 and 210 words and structured into 2-4 paragraphs. Then, generate one "{question1_type}" question, one "{question2_type}" question, one "{question3_type}" question, one "{question4_type}" question, and one "{question5_type}" question. Each question must have one correct answer and three plausible distractors. Adhere to the JSON schema provided in the system prompt.',
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
function generateAcademicPassage(topic, outputRow) {
  const sheet = getSheetByGid(CONFIG['TARGET_SHEET_GID']);
  if (!sheet) {
    Logger.log("Error: Target sheet with GID " + CONFIG['TARGET_SHEET_GID'] + " not found.");
    return;
  }
  Logger.log("Generating passage for topic: " + topic);

  const questionTypes = getQuestionTypes();
  const genre = 'academic passage'; // Fixed genre for academic passages

  const generatedContent = generatePassageWithAI(topic, genre, questionTypes[0], questionTypes[1], questionTypes[2], questionTypes[3], questionTypes[4]);
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
function generatePassageWithAI(topic, genre, question1_type, question2_type, question3_type, question4_type, question5_type) {
  const prompt = buildPassagePrompt(topic, genre, question1_type, question2_type, question3_type, question4_type, question5_type);

  const payload = {
    model: CONFIG['MODEL'],
    messages: [
      {
        role: "system",
        content: CONFIG['System Prompt'] + "\n\nHere is the JSON schema to follow:\n" + CONFIG['JSON Output Schema']
      },
      {
        role: "user",
        content: prompt
      }
    ],
    temperature: CONFIG['TEMPERATURE'],
    max_completion_tokens: CONFIG['MAX_COMPLETION_TOKENS']
  };

  Logger.log("API Request Payload: " + JSON.stringify(payload, null, 2));
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
function buildPassagePrompt(topic, genre, question1_type, question2_type, question3_type, question4_type, question5_type) {
  let prompt = CONFIG['User Prompt Template'] || ''; // Fallback to empty string
  prompt = prompt.replace(/{topic}/g, topic);
  prompt = prompt.replace(/{genre}/g, genre);
  prompt = prompt.replace(/{question1_type}/g, question1_type);
  prompt = prompt.replace(/{question2_type}/g, question2_type);
  prompt = prompt.replace(/{question3_type}/g, question3_type);
  prompt = prompt.replace(/{question4_type}/g, question4_type);
  prompt = prompt.replace(/{question5_type}/g, question5_type);
  return prompt;
}

function getQuestionTypes() {
  const sheet = getSheetByGid(CONFIG['TARGET_SHEET_GID']);
  if (!sheet) {
    Logger.log("Error: Target sheet with GID " + CONFIG['TARGET_SHEET_GID'] + " not found. Using default question types.");
    return ['Vocabulary', 'Factual Info', 'Inference', 'Author\'s Purpose', 'Insert Text'];
  }
  const mode = sheet.getRange('D1').getValue();

  if (mode && mode !== "General Distribution") {
    return [mode, mode, mode, mode, mode];
  }

  // General Distribution Logic for Academic Passages (5 questions)
  const questionTypes = [
    { type: 'Vocabulary', weightConfigKey: 'Vocabulary Question %', orderConstraint: 'first', minCount: 0, maxCount: 1, firstQuestionChance: 0.8 },
    { type: 'Factual Info', weightConfigKey: 'Factual Info Question %', orderConstraint: 'middle', minCount: 1, maxCount: 2 },
    { type: 'Negative Factual Info', weightConfigKey: 'Negative Factual Info Question %', orderConstraint: 'mixed', minCount: 0, maxCount: 1 },
    { type: 'Author\'s Purpose', weightConfigKey: 'Author\'s Purpose Question %', orderConstraint: 'middle-late', minCount: 1, maxCount: 2 },
    { type: 'Organization', weightConfigKey: 'Organization Question %', orderConstraint: 'any', minCount: 0, maxCount: 1 },
    { type: 'Insert Text', weightConfigKey: 'Insert Text Question %', orderConstraint: 'last', minCount: 0, maxCount: 1 },
    { type: 'Inference', weightConfigKey: 'Inference Question %', orderConstraint: 'middle', minCount: 1, maxCount: 2 },
    { type: 'Gist Content', weightConfigKey: 'Gist Content Question %', orderConstraint: 'first', minCount: 0, maxCount: 1, firstQuestionChance: 1.0 }, // Gist Content is almost always first if present
    { type: 'Click on the Sentence', weightConfigKey: 'Click on the Sentence %', orderConstraint: 'any', minCount: 0, maxCount: 1 }
  ];

  let selectedTypes = [];
  let availableTypes = [...questionTypes];

  // Prioritize Gist Content and Vocabulary for the first question
  // Gist Content is almost always first if present (10-15% of passages)
  // Vocabulary is 80% of the time the first question
  
  // Handle Gist Content first
  if (Math.random() < CONFIG['Gist Content Question %']) {
    selectedTypes.push('Gist Content');
    availableTypes = availableTypes.filter(t => t.type !== 'Gist Content'); // Remove Gist Content from further selection
  } else if (Math.random() < CONFIG['Vocabulary Question %']) { // Then handle Vocabulary
    selectedTypes.push('Vocabulary');
    availableTypes = availableTypes.filter(t => t.type !== 'Vocabulary'); // Remove Vocabulary from further selection
  } else {
    // If neither, pick a random type for the first question
    selectedTypes.push(getRandomType(availableTypes));
  }

  // Fill remaining questions
  while (selectedTypes.length < 5) {
    let nextType = getRandomType(availableTypes);

    // Apply constraints for single-occurrence types
    if (nextType === 'Negative Factual Info' && selectedTypes.includes('Negative Factual Info')) {
      availableTypes = availableTypes.filter(t => t.type !== 'Negative Factual Info');
      continue;
    }
    if (nextType === 'Organization' && selectedTypes.includes('Organization')) {
      availableTypes = availableTypes.filter(t => t.type !== 'Organization');
      continue;
    }
    if (nextType === 'Insert Text' && selectedTypes.includes('Insert Text')) {
      availableTypes = availableTypes.filter(t => t.type !== 'Insert Text');
      continue;
    }
    if (nextType === 'Gist Content' && selectedTypes.includes('Gist Content')) {
      availableTypes = availableTypes.filter(t => t.type !== 'Gist Content');
      continue;
    }
    if (nextType === 'Vocabulary' && selectedTypes.includes('Vocabulary')) {
      availableTypes = availableTypes.filter(t => t.type !== 'Vocabulary');
      continue;
    }
    if (nextType === 'Click on the Sentence' && selectedTypes.includes('Click on the Sentence')) {
      availableTypes = availableTypes.filter(t => t.type !== 'Click on the Sentence');
      continue;
    }

    // Apply max count constraints for other types
    const typeCount = selectedTypes.filter(t => t === nextType).length;
    const typeDef = questionTypes.find(t => t.type === nextType);
    if (typeDef && typeCount >= typeDef.maxCount) {
      availableTypes = availableTypes.filter(t => t.type !== nextType);
      continue;
    }

    selectedTypes.push(nextType);
  }

  // Final ordering based on constraints (simplified for now, more complex logic might be needed)
  // This part would ideally involve sorting based on 'orderConstraint'
  // For now, we'll just return the selected types.
  // A more robust solution would involve a more sophisticated scheduling algorithm.
  return selectedTypes;
}

function getRandomType(types) {
    const rand = Math.random();
    let cumulative = 0;

    // Create a weighted list
    const weightedList = types.map(t => ({ type: t.type, weight: CONFIG[t.weightConfigKey] || 0 }));
    const totalWeight = weightedList.reduce((sum, item) => sum + item.weight, 0);

    // Normalize weights and select type
    for (const item of weightedList) {
        cumulative += item.weight / totalWeight;
        if (rand < cumulative) {
            return item.type;
        }
    }
    return weightedList[weightedList.length - 1].type; // Fallback
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
  generateAcademicPassage(topic, nextEmptyRow);
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

// Menu function to add custom menu item
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('TOEFL Academic Passages')
    .addItem('Generate Single Passage', 'generateSinglePassage')
    .addSeparator()
    .addItem('Start Batch Process', 'startBatchProcess')
    .addItem('Stop Batch Process', 'stopBatchProcess')
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
