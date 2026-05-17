/**
 * Voice-activated unlock example using Vosk (offline speech recognition).
 *
 * Requirements:
 *   npm install vosk mic
 *   Download a Vosk model from https://alphacephei.com/vosk/models
 *   and extract to ./vosk-model-small-en-us (or adjust MODEL_PATH).
 *
 * Usage:
 *   node example-voice.js <username> <password> [domain]
 */

"use strict";

const vosk = require("vosk");
const mic = require("mic");
const { CredentialProviderClient } = require("./credential-provider");

const MODEL_PATH = "./vosk-model-small-en-us";
const TRIGGER_PHRASES = ["unlock", "unlock computer", "open sesame"];

async function voiceUnlock(username, password, domain = ".") {
  const client = new CredentialProviderClient();

  if (!require("fs").existsSync(MODEL_PATH)) {
    console.error(`Model not found at ${MODEL_PATH}.`);
    console.error("Download from https://alphacephei.com/vosk/models");
    process.exit(1);
  }

  vosk.setLogLevel(-1);
  const model = new vosk.Model(MODEL_PATH);
  const recognizer = new vosk.Recognizer({ model, sampleRate: 16000 });

  const micInstance = mic({
    rate: "16000",
    channels: "1",
    encoding: "signed-integer",
    bitwidth: "16",
  });

  const micStream = micInstance.getAudioStream();
  console.log('Listening. Say "unlock computer" to unlock the workstation.');
  console.log("Press Ctrl+C to stop.\n");
  micInstance.start();

  micStream.on("data", async (data) => {
    if (recognizer.acceptWaveform(data)) {
      const { text } = recognizer.result();
      if (!text) return;

      console.log(`Heard: "${text}"`);

      const matched = TRIGGER_PHRASES.some((phrase) =>
        text.toLowerCase().includes(phrase)
      );
      if (matched) {
        micInstance.stop();
        console.log("Voice command matched. Sending unlock...");
        try {
          const result = await client.unlockWithRetry(
            username,
            password,
            domain
          );
          console.log(`Result: ${result.response}`);
        } catch (err) {
          console.error(`Unlock failed: ${err.message}`);
        }
        process.exit(0);
      }
    }
  });
}

const args = process.argv.slice(2);
if (args.length < 2) {
  console.log("Usage: node example-voice.js <username> <password> [domain]");
  process.exit(1);
}
voiceUnlock(args[0], args[1], args[2] || ".");
