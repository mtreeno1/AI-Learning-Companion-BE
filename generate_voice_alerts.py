"""
Generate voice alerts using Edge TTS (Microsoft Azure TTS)
High quality Vietnamese voices - FREE! 
"""

import asyncio
import edge_tts
import os

# Create assets directory
os.makedirs('assets', exist_ok=True)


# Vietnamese voices available
VIETNAMESE_VOICES = {
    'female_north': 'vi-VN-HoaiMyNeural',      # Nữ - Miền Bắc (tự nhiên)
    'male_north': 'vi-VN-NamMinhNeural',       # Nam - Miền Bắc
}


async def generate_voice(text: str, output_file: str, voice:  str = 'vi-VN-HoaiMyNeural', rate: str = '+0%', volume: str = '+0%'):
    """
    Generate voice from text using Edge TTS
    
    Args:
        text: Text to convert to speech
        output_file: Output filename (e.g., 'assets/alert.mp3')
        voice: Voice ID (see VIETNAMESE_VOICES)
        rate: Speaking rate (-50% to +100%, default +0%)
        volume: Volume (-50% to +50%, default +0%)
    """
    print(f"🎙️ Generating:  {output_file}")
    print(f"   Text: {text}")
    print(f"   Voice: {voice}")
    
    communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
    await communicate.save(output_file)
    
    print(f"✅ Saved:  {output_file}\n")


async def generate_all_alerts():
    """Generate all alert voices"""
    
    print("=" * 70)
    print("🎤 GENERATING AI VOICE ALERTS")
    print("=" * 70)
    print()
    
    # Alert messages
    alerts = {
        'gentle':  {
            'text': 'Bạn đang trong quá trình học tập, hãy tập trung nào',
            'file': 'assets/gentle_voice_alert.mp3',
            'voice':  VIETNAMESE_VOICES['female_north'],
            'rate': '+0%',
            'volume': '+0%'
        },
        'urgent': {
            'text':  'Chú ý! Bạn đã mất tập trung quá lâu.  Hãy quay lại bài học nhé',
            'file': 'assets/urgent_voice_alert.mp3',
            'voice':  VIETNAMESE_VOICES['female_north'],
            'rate':  '+5%',  # Nói nhanh hơn 5%
            'volume': '+10%'  # To hơn 10%
        },
        'motivational': {
            'text':  'Bạn làm rất tốt! Hãy tiếp tục duy trì sự tập trung nhé',
            'file': 'assets/motivational_voice. mp3',
            'voice':  VIETNAMESE_VOICES['female_north'],
            'rate':  '-5%',  # Nói chậm hơn, dễ nghe
            'volume': '+0%'
        }
    }
    
    # Generate each alert
    for alert_type, config in alerts.items():
        await generate_voice(
            text=config['text'],
            output_file=config['file'],
            voice=config['voice'],
            rate=config['rate'],
            volume=config['volume']
        )
    
    print("=" * 70)
    print("✅ ALL VOICE ALERTS GENERATED SUCCESSFULLY!")
    print("=" * 70)
    print("\nFiles created:")
    for alert_type, config in alerts.items():
        print(f"  - {config['file']}")
        print(f"    → {config['text']}")
    print()


async def list_available_voices():
    """List all available Vietnamese voices"""
    print("\n🎙️ Available Vietnamese Voices:\n")
    
    voices = await edge_tts.list_voices()
    
    for voice in voices:
        if voice['Locale']. startswith('vi-'):
            print(f"Voice ID: {voice['ShortName']}")
            print(f"  Name: {voice['FriendlyName']}")
            print(f"  Gender: {voice['Gender']}")
            print(f"  Locale: {voice['Locale']}")
            print()


async def test_voice_preview(text: str = "Xin chào, đây là giọng đọc tiếng Việt"):
    """Test different voices"""
    print("\n🎧 TESTING VOICES\n")
    
    for name, voice_id in VIETNAMESE_VOICES. items():
        output = f"assets/test_{name}.mp3"
        print(f"Testing {name} ({voice_id})...")
        await generate_voice(text, output, voice_id)


if __name__ == "__main__": 
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "list":
            # List available voices
            asyncio. run(list_available_voices())
        
        elif command == "test": 
            # Test voices with sample text
            asyncio.run(test_voice_preview())
        
        elif command == "custom":
            # Generate custom message
            if len(sys.argv) < 3:
                print("Usage: python generate_voice_alerts.py custom 'Your message here'")
                sys. exit(1)
            
            custom_text = sys.argv[2]
            output_file = "assets/custom_voice. mp3"
            
            asyncio.run(generate_voice(
                custom_text,
                output_file,
                VIETNAMESE_VOICES['female_north']
            ))
        
        else:
            print("Unknown command.  Available: list, test, custom")
    
    else:
        # Default:  Generate all alerts
        asyncio.run(generate_all_alerts())