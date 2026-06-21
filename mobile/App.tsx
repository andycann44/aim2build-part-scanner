import { useRef, useState } from 'react';
import { Button, Image, SafeAreaView, Text, View } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';

export default function App() {
  const cameraRef = useRef<CameraView | null>(null);
  const [permission, requestPermission] = useCameraPermissions();
  const [photoUri, setPhotoUri] = useState<string | null>(null);

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
    const photo = await cameraRef.current?.takePictureAsync({ quality: 0.8 });
    if (photo?.uri) setPhotoUri(photo.uri);
  }

  if (photoUri) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: '#111' }}>
        <Image source={{ uri: photoUri }} style={{ flex: 1 }} resizeMode="contain" />
        <Button title="Scan Another" onPress={() => setPhotoUri(null)} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#111' }}>
      <Text style={{ color: 'white', textAlign: 'center', padding: 12 }}>
        Aim2Build Part Scanner - Black Parts Only
      </Text>
      <CameraView
        ref={cameraRef}
        style={{ flex: 1 }}
        facing="back"
      />
      <Button title="Take Photo" onPress={takePhoto} />
    </SafeAreaView>
  );
}
