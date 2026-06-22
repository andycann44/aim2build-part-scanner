import { useRef, useState } from 'react';
import { Button, Image, SafeAreaView, ScrollView, Text, View } from 'react-native';
import Slider from '@react-native-community/slider';
import { CameraView, useCameraPermissions } from 'expo-camera';


function GridOverlay({ guideSize }: { guideSize: 2 | 4 | 6 | 8 }) {
  const lines = Array.from({ length: 13 });

  return (
    <View
      pointerEvents="none"
      style={{
        position: 'absolute',
        left: '50%',
        top: '50%',
        width: '92%',
        aspectRatio: 1,
        transform: [{ translateX: '-50%' }, { translateY: '-50%' }],
      }}
    >
      {lines.map((_, i) => (
        <View
          key={`v-${i}`}
          style={{
            position: 'absolute',
            left: `${(i / 12) * 100}%`,
            top: 0,
            bottom: 0,
            width: i === 0 || i === 12 ? 2 : 1,
            backgroundColor: 'rgba(255,255,255,0.28)',
          }}
        />
      ))}

      {lines.map((_, i) => (
        <View
          key={`h-${i}`}
          style={{
            position: 'absolute',
            top: `${(i / 12) * 100}%`,
            left: 0,
            right: 0,
            height: i === 0 || i === 12 ? 2 : 1,
            backgroundColor: 'rgba(255,255,255,0.28)',
          }}
        />
      ))}

      <View
        style={{
          position: 'absolute',
          left: `${((12 - guideSize) / 2 / 12) * 100}%`,
          top: `${((12 - guideSize) / 2 / 12) * 100}%`,
          width: `${(guideSize / 12) * 100}%`,
          height: `${(guideSize / 12) * 100}%`,
          borderWidth: 3,
          borderColor: guideSize <= 2 ? 'rgba(0,255,120,0.95)' : 'rgba(255,230,0,0.95)',
          backgroundColor: 'rgba(255,255,255,0.04)',
        }}
      />

      <Text
        style={{
          position: 'absolute',
          left: 8,
          bottom: 8,
          color: 'white',
          backgroundColor: 'rgba(0,0,0,0.55)',
          padding: 6,
          borderRadius: 6,
          fontSize: 12,
        }}
      >
        12x12 grid | target guide
      </Text>
    </View>
  );
}


export default function App() {
  const cameraRef = useRef<any>(null);
  const [permission, requestPermission] = useCameraPermissions();

  const [photos, setPhotos] = useState<string[]>([]);
  const [status, setStatus] = useState('Ready');
  const [zoom, setZoom] = useState(0);
  const [flash, setFlash] = useState<'off' | 'on'>('off');
  const [guideSize, setGuideSize] = useState<2 | 4 | 6 | 8>(4);

  if (!permission) return null;

  if (!permission.granted) {
    return (
      <SafeAreaView style={{ flex: 1, justifyContent: 'center', padding: 20 }}>
        <Text style={{ textAlign: 'center', marginBottom: 20 }}>
          Aim2Build Scanner needs camera access.
        </Text>
        <Button title="Allow Camera" onPress={requestPermission} />
      </SafeAreaView>
    );
  }

  async function takePhoto() {
    try {
      setStatus('Taking photo...');
      const photo = await cameraRef.current?.takePictureAsync({ quality: 1 });

      if (!photo?.uri) {
        setStatus('No photo URI returned');
        return;
      }

      setPhotos((prev) => [...prev, photo.uri]);
      setStatus(`Saved shot ${photos.length + 1}`);
    } catch (err: any) {
      setStatus(`CAPTURE ERROR: ${err?.message || String(err)}`);
    }
  }

  async function uploadSession() {
    if (photos.length < 3) return;

    setStatus('Uploading...');
    const form = new FormData();

    photos.forEach((uri, index) => {
      form.append('files', {
        uri,
        name: `photo_${index + 1}.jpg`,
        type: 'image/jpeg',
      } as any);
    });

    const res = await fetch('http://192.168.0.230:8787/api/sessions', {
      method: 'POST',
      body: form,
      headers: { 'Content-Type': 'multipart/form-data' },
    });

    const json = await res.json();
    setStatus(`Uploaded: ${json.session_id}`);
  }

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#111' }}>
      <Text style={{ color: 'white', textAlign: 'center', padding: 8, fontWeight: '700' }}>
        Aim2Build Part Scanner
      </Text>

      <Text style={{ color: 'white', textAlign: 'center', paddingBottom: 6 }}>
        Black / color_id 0 | Shots: {photos.length}/3
      </Text>

      <View style={{ flex: 1 }}>
        <CameraView
          ref={cameraRef}
          style={{ flex: 1 }}
          facing="back"
          zoom={zoom}
          flash={flash}
        />
        <GridOverlay guideSize={guideSize} />
      </View>

      <Text style={{ color: 'white', textAlign: 'center' }}>
        Zoom: {Math.round(zoom * 100)}%
      </Text>

      <Slider
        minimumValue={0}
        maximumValue={0.8}
        value={zoom}
        onValueChange={setZoom}
      />

      <View style={{ flexDirection: 'row', justifyContent: 'space-around' }}>
        <Button title="1x" onPress={() => setZoom(0)} />
        <Button title="2x" onPress={() => setZoom(0.25)} />
        <Button title="3x" onPress={() => setZoom(0.45)} />
        <Button title="Auto Fit" onPress={() => setZoom(0.35)} />
      </View>

      <Text style={{ color: 'white', textAlign: 'center', paddingTop: 6 }}>
        Target guide: {guideSize}x{guideSize} studs
      </Text>

      <View style={{ flexDirection: 'row', justifyContent: 'space-around' }}>
        <Button title="2x2" onPress={() => setGuideSize(2)} />
        <Button title="4x4" onPress={() => setGuideSize(4)} />
        <Button title="6x6" onPress={() => setGuideSize(6)} />
        <Button title="8x8" onPress={() => setGuideSize(8)} />
      </View>

      <Button
        title={`Flash: ${flash.toUpperCase()}`}
        onPress={() => setFlash(flash === 'off' ? 'on' : 'off')}
      />

      <Button
        title={photos.length < 3 ? `Take Shot ${photos.length + 1}/3` : 'Add More Shot'}
        onPress={takePhoto}
      />

      <Button
        title={photos.length >= 3 ? 'Finish Session - Upload' : 'Finish Session - Need 3 Photos'}
        disabled={photos.length < 3}
        onPress={uploadSession}
      />

      <Button title="Reset Session" onPress={() => setPhotos([])} />

      <Text style={{ color: 'white', textAlign: 'center', padding: 8 }}>{status}</Text>

      <ScrollView horizontal style={{ maxHeight: 90, padding: 6 }}>
        {photos.map((uri, index) => (
          <View key={uri} style={{ marginRight: 8 }}>
            <Image source={{ uri }} style={{ width: 70, height: 70, borderRadius: 6 }} />
            <Text style={{ color: 'white', textAlign: 'center' }}>#{index + 1}</Text>
          </View>
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}
