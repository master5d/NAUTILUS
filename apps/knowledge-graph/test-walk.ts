import { walkVault } from './src/lib/sources/obsidian'

console.log('🧪 Testing walkVault & Mentions Extraction\n')
const vaultPath = 'C:\\Users\\sasha\\Downloads\\Notes_ACE'

try {
  let count = 0
  for (const note of walkVault(vaultPath)) {
    if (note.cluster === 'Calendar') {
      console.log(`📅 Daily Log Found: ${note.title}`)
      console.log(`   Path: ${note.filePath}`)
      console.log(`   Mentions:`, note.mentions)
      console.log(`   Tags:`, note.tags)
      console.log(`   Content Preview: ${note.content.slice(0, 100)}...\n`)
      count++
    }
  }
  console.log(`🏁 Test complete. Found ${count} daily logs.`)
} catch (err) {
  console.error('❌ Test failed:', err)
}
