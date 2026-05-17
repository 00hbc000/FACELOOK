/**
 * Face-recognition unlock example using @vladmandic/face-api + canvas.
 *
 * Requirements:
 *   npm install @vladmandic/face-api canvas
 *   Download face-api models to ./models directory.
 *   A webcam capture mechanism (platform-specific, see note below).
 *
 * Usage:
 *   node example-face.js <reference_image> <username> <password> [domain]
 *
 * Note: Node.js has no built-in webcam API. For production use,
 * consider an Electron app (which has getUserMedia) or use a
 * native addon like opencv4nodejs.
 */

"use strict";

const faceapi = require("@vladmandic/face-api");
const canvas = require("canvas");
const fs = require("fs");
const { CredentialProviderClient } = require("./credential-provider");

// Patch face-api for Node.js
const { Canvas, Image, ImageData } = canvas;
faceapi.env.monkeyPatch({ Canvas, Image, ImageData });

const MODELS_PATH = "./models";
const MATCH_THRESHOLD = 0.5;

async function faceUnlock(
  knownFacePath,
  username,
  password,
  domain = "."
) {
  const client = new CredentialProviderClient();

  if (!fs.existsSync(MODELS_PATH)) {
    console.error(`Models directory not found at ${MODELS_PATH}.`);
    console.error(
      "Download from https://github.com/vladmandic/face-api/tree/master/model"
    );
    process.exit(1);
  }

  console.log("Loading face-api models...");
  await faceapi.nets.ssdMobilenetv1.loadFromDisk(MODELS_PATH);
  await faceapi.nets.faceLandmark68Net.loadFromDisk(MODELS_PATH);
  await faceapi.nets.faceRecognitionNet.loadFromDisk(MODELS_PATH);

  console.log(`Loading reference face from ${knownFacePath}...`);
  const knownImg = await canvas.loadImage(knownFacePath);
  const knownDetection = await faceapi
    .detectSingleFace(knownImg)
    .withFaceLandmarks()
    .withFaceDescriptor();

  if (!knownDetection) {
    console.error("No face found in the reference image.");
    process.exit(1);
  }

  const matcher = new faceapi.FaceMatcher(knownDetection, MATCH_THRESHOLD);
  console.log("Reference face loaded.");
  console.log(
    "In production, capture webcam frames here and compare each one."
  );
  console.log("Simulating a match for demonstration...\n");

  // ------------------------------------------------------------------
  // In a real application you would capture a webcam frame here, run
  // face detection on it, and compare the descriptor against `matcher`.
  //
  // Example with opencv4nodejs:
  //   const cv = require('opencv4nodejs');
  //   const cap = new cv.VideoCapture(0);
  //   const frame = cap.read();
  //   const img = await canvas.loadImage(cv.imencode('.jpg', frame));
  //   const det = await faceapi.detectSingleFace(img)
  //                     .withFaceLandmarks().withFaceDescriptor();
  //   if (det) {
  //     const match = matcher.findBestMatch(det.descriptor);
  //     if (match.label !== 'unknown') { /* unlock */ }
  //   }
  // ------------------------------------------------------------------

  // Demonstrate the unlock call (skip actual webcam capture):
  console.log("Sending unlock command...");
  try {
    const result = await client.unlockWithRetry(username, password, domain);
    console.log(`Result: ${result.response}`);
  } catch (err) {
    console.error(`Unlock failed: ${err.message}`);
  }
}

const args = process.argv.slice(2);
if (args.length < 3) {
  console.log(
    "Usage: node example-face.js <reference_image> <username> <password> [domain]"
  );
  process.exit(1);
}
faceUnlock(args[0], args[1], args[2], args[3] || ".");
