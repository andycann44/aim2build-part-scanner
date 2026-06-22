import { useRef, useState } from 'react';
import * as Device from 'expo-device';
import { Button, Image, Pressable, SafeAreaView, ScrollView, Text, View } from 'react-native';
import Slider from '@react-native-community/slider';
import { CameraView, useCameraPermissions } from 'expo-camera';

export default function App() {
  const cameraRef = useRef<CameraView | null>(null);
  const [permission, requestPermission] = useCameraPermissions();
  const [photos, setPhotos] = useState<string[]>([]);
  const [flash, setFlash] = useState<'off' | 'on'>('off');
  const [status, setStatus] = useState('');
  const [zoom, setZoom] = useState(0);
  const [focusPoint, setFocusPoint] = useState<{ x: number; y: number } | null>(null);

  if (!permission) return <View />;

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
    const photo = await cameraRef.current?.takePictureAsync({ quality: 1 });
    if (photo?.uri) setPhotos((prev) => [...prev, photo.uri]);
  }

  function resetSession() {
    setPhotos([]);
  }

  const minimumReady = photos.length >= 3;

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#111' }}>
      <Text style={{ color: 'white', textAlign: 'center', padding: 10, fontWeight: '700' }}>
        Aim2Build Black Part Scanner\n{Device.modelName || 'Unknown device'}
      </Text>

      <Text style={{ color: 'white', textAlign: 'center', paddingBottom: 8 }}>
        color_id 0 / Black | Shots: {photos.length}/3 minimum
      </Text>

      <Pressable
        style={{ flex: 1 }}
        onPress={(e) => {
          setFocusPoint({ x: e.nativeEvent.locationX, y: e.nativeEvent.locationY });
          setStatus('Focus point set - hold steady');
        }}
      >
        <CameraView
          ref={cameraRef}
          style={{ flex: 1 }}
          facing="back"
          flash={flash}
          zoom={zoom}
        />
        {focusPoint && (
          <View
            pointerEvents="none"
            style={{
              position: 'absolute',
              left: focusPoint.x - 25,
              top: focusPoint.y - 25,
              width: 50,
              height: 50,
              borderWidth: 2,
              borderColor: 'yellow',
              borderRadius: 25,
            }}
          />
        )}
      </Pressable>

      <Text style={{ color: 'white', textAlign: 'center' }}>
        Zoom: {Math.round(zoom * 100)}%
      </Text>
      <Slider
        minimumValue={0}
        maximumValue={0.7}
        value={zoom}
        onValueChange={setZoom}
      />

      <Button
        title={`Flash: ${flash.toUpperCase()}`}
        onPress={() => setFlash(flash === 'off' ? 'on' : 'off')}
      />

      <Button
        title={photos.length < 3 ? `Take Shot ${photos.length + 1}/3` : 'Add More Shot'}
        onPress={takePhoto}
      />

      <Button
        title={minimumReady ? 'Finish Session - Ready' : 'Finish Session - Need 3 Photos'}
        disabled={!minimumReady}
        onPress={async () => {
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
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          });

          const json = await res.json();
          setStatus(`Uploaded: ${json.session_id}`);
        }}
      />

      <Button title="Reset Session" onPress={resetSession} />

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
