import { useState } from 'react';
import { Button, Image, SafeAreaView, Text, View } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';

export default function App() {
  const [permission, requestPermission] = useCameraPermissions();
  const [photo, setPhoto] = useState<string | null>(null);
  const [cameraRef, setCameraRef] = useState<any>(null);

  if (!permission) return <View />;

  if (!permission.granted) {
    return (
      <SafeAreaView style={{ flex: 1, justifyContent: 'center' }}>
        <Button title="Allow Camera" onPress={requestPermission} />
      </SafeAreaView>
    );
  }

  async function takePhoto() {
    if (!cameraRef) return;
    const result = await cameraRef.takePictureAsync();
    setPhoto(result.uri);
  }

  if (photo) {
    return (
      <SafeAreaView style={{ flex: 1 }}>
        <Image
          source={{ uri: photo }}
          style={{ flex: 1 }}
          resizeMode="contain"
        />
        <Button title="Scan Another" onPress={() => setPhoto(null)} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={{ flex: 1 }}>
      <Text style={{ textAlign: 'center', padding: 10 }}>
        Aim2Build Part Scanner v0.0.1
      </Text>

      <CameraView
        style={{ flex: 1 }}
        facing="back"
        ref={(r) => setCameraRef(r)}
      />

      <Button title="Take Photo" onPress={takePhoto} />
    </SafeAreaView>
  );
}
