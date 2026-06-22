import { useRef, useState } from 'react';
import { Button, Image, SafeAreaView, ScrollView, Text, View } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import {
  Camera,
  useCameraDevice,
  useCameraPermission,
} from 'react-native-vision-camera';


function GridOverlay() {
  const lines = Array.from({ length: 13 });

  return (
    <View pointerEvents="none" style={{ position: 'absolute', inset: 0 }}>
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
          left: '33.333%',
          top: '33.333%',
          width: '33.333%',
          height: '33.333%',
          borderWidth: 2,
          borderColor: 'rgba(255,230,0,0.95)',
        }}
      />

      <View
        style={{
          position: 'absolute',
          left: '41.666%',
          top: '41.666%',
          width: '16.666%',
          height: '16.666%',
          borderWidth: 2,
          borderColor: 'rgba(0,255,120,0.95)',
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
        12x12 grid | yellow 4x4 | green 2x2
      </Text>
    </View>
  );
}


export default function App() {
  const cameraRef = useRef<any>(null);
  const { hasPermission, requestPermission } = useCameraPermission();
  const device = useCameraDevice('back');

  const [photos, setPhotos] = useState<string[]>([]);
  const [status, setStatus] = useState('Ready');

  if (!hasPermission) {
    return (
      <SafeAreaView style={{ flex: 1, justifyContent: 'center', padding: 20 }}>
        <Text style={{ textAlign: 'center', marginBottom: 20 }}>
          Aim2Build Scanner needs camera access.
        </Text>
        <Button title="Allow Camera" onPress={requestPermission} />
      </SafeAreaView>
    );
  }

  if (!device) {
    return (
      <SafeAreaView style={{ flex: 1, justifyContent: 'center', padding: 20 }}>
        <Text>No back camera found.</Text>
      </SafeAreaView>
    );
  }

  async function takePhoto() {
    try {
      setStatus('Opening camera...');

      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        quality: 1,
        allowsEditing: false,
        exif: true,
      });

      if (result.canceled || !result.assets?.[0]?.uri) {
        setStatus('Camera cancelled');
        return;
      }

      const uri = result.assets[0].uri;
      setPhotos((prev) => [...prev, uri]);
      setStatus(`Saved shot ${photos.length + 1}`);
    } catch (err: any) {
      setStatus(`CAPTURE ERROR: ${err?.message || String(err)}`);
      console.log('CAPTURE ERROR', err);
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
        <Camera
          ref={cameraRef}
          style={{ flex: 1 }}
          device={device}
          isActive={true}
        />
        <GridOverlay />
      </View>

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
