import { useEffect, useRef, useState } from 'react';
import { Button, Image, SafeAreaView, ScrollView, Text, View } from 'react-native';
import Slider from '@react-native-community/slider';
import {
  Camera,
  useCameraDevice,
  useCameraPermission,
} from 'react-native-vision-camera';

export default function App() {
  const cameraRef = useRef<React.ElementRef<typeof Camera>>(null);
  const { hasPermission, requestPermission } = useCameraPermission();
  const device = useCameraDevice('back');
  const [photos, setPhotos] = useState<string[]>([]);
  const [zoom, setZoom] = useState(1);
  const [status, setStatus] = useState('Camera ready - test capture');
  const [cameraReady, setCameraReady] = useState(true);

  useEffect(() => {
    if (!hasPermission) requestPermission();
  }, [hasPermission]);

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
      if (!cameraRef.current) {
        setStatus('Camera not ready: ref missing');
        return;
      }

      if (!cameraReady) {
        setStatus('Camera not ready yet');
        return;
      }

      setStatus('Taking photo...');

      const photo = await cameraRef.current.takePhoto({
        flash: 'off',
        enableShutterSound: false,
      });

      if (!photo?.path) {
        setStatus('No photo path returned');
        return;
      }

      const uri = photo.path.startsWith('file://') ? photo.path : `file://${photo.path}`;
      setPhotos((prev) => [...prev, uri]);
      setStatus(`Shot saved: ${photos.length + 1}`);
    } catch (err: any) {
      setStatus(`Camera error: ${err?.message || String(err)}`);
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
      <Text style={{ color: 'white', textAlign: 'center', padding: 10, fontWeight: '700' }}>
        Aim2Build Part Scanner
      </Text>

      <Text style={{ color: 'white', textAlign: 'center', paddingBottom: 8 }}>
        Black / color_id 0 | Shots: {photos.length}/3 minimum
      </Text>

      <Camera
        ref={cameraRef}
        style={{ flex: 1 }}
        device={device}
        isActive={true}
        zoom={zoom}
      />

      <Text style={{ color: 'white', textAlign: 'center' }}>
        Zoom: {zoom.toFixed(1)}x | Min {device.minZoom.toFixed(1)} / Max {Math.min(device.maxZoom, 6).toFixed(1)}
      </Text>

      <Slider
        minimumValue={device.minZoom}
        maximumValue={Math.min(device.maxZoom, 6)}
        value={zoom}
        onValueChange={setZoom}
      />

      <View style={{ flexDirection: 'row', justifyContent: 'space-around' }}>
        <Button title="1x" onPress={() => setZoom(Math.max(device.minZoom, 1))} />
        <Button title="2x" onPress={() => setZoom(Math.min(Math.max(device.minZoom, 2), Math.min(device.maxZoom, 6)))} />
        <Button title="3x" onPress={() => setZoom(Math.min(Math.max(device.minZoom, 3), Math.min(device.maxZoom, 6)))} />
      </View>

      <Button
        title={photos.length < 3 ? `Take Shot ${photos.length + 1}/3` : 'Add More Shot'}
        onPress={takePhoto}
        disabled={!cameraReady}
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
