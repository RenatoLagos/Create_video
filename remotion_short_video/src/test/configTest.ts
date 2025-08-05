/**
 * Test script to verify the dynamic configuration system
 * Run this in the browser console or as a Node.js script
 */

import { configSwitcher } from '../utils/configSwitcher';
import { getAllVideoConfigs, getVideoConfig } from '../utils/configLoader';

/**
 * Test all configuration loading functions
 */
export function testConfigSystem() {
  console.log('🧪 Testing Dynamic Video Configuration System...\n');

  // Test 1: Load all configurations
  console.log('1️⃣ Testing getAllVideoConfigs()');
  const allConfigs = getAllVideoConfigs();
  console.log(`   ✅ Loaded ${allConfigs.length} configurations`);
  allConfigs.forEach(config => {
    console.log(`   - ${config.id}: ${config.title} (${config.layout})`);
  });

  // Test 2: Load specific configuration
  console.log('\n2️⃣ Testing getVideoConfig()');
  const specificConfig = getVideoConfig('spanish-lesson-center');
  if (specificConfig) {
    console.log('   ✅ Loaded specific config:', specificConfig.title);
    console.log('   - Layout:', specificConfig.layout);
    console.log('   - Font:', specificConfig.subtitlesConfig.fontFamily);
    console.log('   - Font Size:', specificConfig.subtitlesConfig.fontSize);
  } else {
    console.log('   ❌ Failed to load specific config');
  }

  // Test 3: Test configSwitcher
  console.log('\n3️⃣ Testing ConfigSwitcher');
  
  // Test by layout
  const circleConfigs = configSwitcher.getConfigsByLayout('circle');
  console.log(`   ✅ Found ${circleConfigs.length} circle layout configs`);
  
  const bottomConfigs = configSwitcher.getConfigsByLayout('bottom');
  console.log(`   ✅ Found ${bottomConfigs.length} bottom layout configs`);
  
  const centerConfigs = configSwitcher.getConfigsByLayout('center');
  console.log(`   ✅ Found ${centerConfigs.length} center layout configs`);

  // Test by font
  const poppinsConfigs = configSwitcher.getConfigsByFont('Poppins');
  console.log(`   ✅ Found ${poppinsConfigs.length} configs using Poppins font`);

  // Test 4: Custom configuration
  console.log('\n4️⃣ Testing Custom Configuration Creation');
  const customConfig = configSwitcher.createCustomConfig('spanish-lesson-center', {
    id: 'custom-test',
    title: 'Custom Test Video',
    subtitlesConfig: {
      fontSize: 80,
      color: '#ff0000',
      fontFamily: 'Nunito'
    }
  });

  if (customConfig) {
    console.log('   ✅ Created custom config:', customConfig.title);
    console.log('   - Font Size:', customConfig.subtitlesConfig.fontSize);
    console.log('   - Color:', customConfig.subtitlesConfig.color);
    console.log('   - Font Family:', customConfig.subtitlesConfig.fontFamily);
  } else {
    console.log('   ❌ Failed to create custom config');
  }

  console.log('\n🎉 Configuration system test completed!');
  return {
    allConfigs,
    specificConfig,
    circleConfigs,
    bottomConfigs,
    centerConfigs,
    poppinsConfigs,
    customConfig
  };
}

/**
 * Test configuration validation
 */
export function testConfigValidation() {
  console.log('\n🔍 Testing Configuration Validation...');
  
  const configs = getAllVideoConfigs();
  let validCount = 0;
  let invalidCount = 0;

  configs.forEach(config => {
    const required = ['id', 'title', 'videoFile', 'subtitlesFile', 'layout'];
    const isValid = required.every(field => config[field as keyof typeof config] !== undefined);
    
    if (isValid) {
      validCount++;
      console.log(`   ✅ ${config.id}: Valid`);
    } else {
      invalidCount++;
      console.log(`   ❌ ${config.id}: Invalid - missing required fields`);
    }
  });

  console.log(`\n📊 Validation Results: ${validCount} valid, ${invalidCount} invalid`);
  return { validCount, invalidCount };
}

// Export for use in browser console
(window as any).testConfigSystem = testConfigSystem;
(window as any).testConfigValidation = testConfigValidation;