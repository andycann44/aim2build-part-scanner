import { useRef, useState } from 'react';
import { Button, Image, SafeAreaView, ScrollView, Text, View } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';

export default function App() {
  const cameraRef = useRef<CameraView | null>(null);
  const [permission, requestPermission] = useCameraPermissions();
  const [photos, setPhotos] = useState<string[]>([]);
  const [flash, setFlash] = useState<'off' | 'on'>('off');

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
        Aim2Build Black Part Scanner
      </Text>

      <Text style={{ color: 'white', textAlign: 'center', paddingBottom: 8 }}>
        color_id 0 / Black | Shots: {photos.length}/3 minimum
      </Text>

      <CameraView
        ref={cameraRef}
        style={{ flex: 1 }}
        facing="back"
        flash={flash}
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
        onPress={() => alert(`Session ready with ${photos.length} photos`)}
      />

      <Button title="Reset Session" onPress={resetSession} />

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
