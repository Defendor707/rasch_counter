import React, {useState} from 'react';
import {
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  Alert,
  Dimensions,
} from 'react-native';
import DocumentPicker from 'react-native-document-picker';
import LinearGradient from 'react-native-linear-gradient';
import ProgressBar from 'react-native-progress/Bar';
import Toast from 'react-native-toast-message';
import Icon from 'react-native-vector-icons/MaterialIcons';

const {width} = Dimensions.get('window');

interface ProcessingStatus {
  status: 'idle' | 'processing' | 'completed' | 'error';
  progress: number;
  message: string;
}

interface Results {
  summary: {
    total_students: number;
    total_questions: number;
    grade_distribution: Record<string, number>;
    average_score: number;
    highest_score: number;
    lowest_score: number;
  };
  item_difficulties: {
    min: number;
    max: number;
    mean: number;
    std: number;
    items: Array<{
      Question: string;
      Difficulty: number;
      Difficulty_Level: string;
    }>;
  };
}

const App = (): JSX.Element => {
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatus>({
    status: 'idle',
    progress: 0,
    message: '',
  });
  const [results, setResults] = useState<Results | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const API_BASE_URL = 'http://localhost:5000'; // Change this to your server URL

  const showToast = (message: string, type: 'success' | 'error' | 'info') => {
    Toast.show({
      type,
      text1: message,
      position: 'top',
    });
  };

  const uploadFile = async () => {
    try {
      const result = await DocumentPicker.pick({
        type: [DocumentPicker.types.xlsx, DocumentPicker.types.xls],
      });

      if (result.length > 0) {
        const file = result[0];
        await processFile(file);
      }
    } catch (err) {
      if (DocumentPicker.isCancel(err)) {
        // User cancelled the picker
      } else {
        showToast('Fayl tanlash xatoligi', 'error');
      }
    }
  };

  const processFile = async (file: any) => {
    try {
      setProcessingStatus({
        status: 'processing',
        progress: 0,
        message: 'Fayl yuklanmoqda...',
      });

      const formData = new FormData();
      formData.append('file', {
        uri: file.uri,
        type: file.type,
        name: file.name,
      });

      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const data = await response.json();

      if (data.success) {
        setSessionId(data.session_id);
        setProcessingStatus({
          status: 'processing',
          progress: 10,
          message: 'Tahlil boshlandi...',
        });
        startProgressMonitoring(data.session_id);
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      showToast(`Yuklash xatoligi: ${error.message}`, 'error');
      setProcessingStatus({
        status: 'error',
        progress: 0,
        message: 'Xatolik yuz berdi',
      });
    }
  };

  const startProgressMonitoring = (sessionId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/status/${sessionId}`);
        const data = await response.json();

        setProcessingStatus({
          status: data.status,
          progress: data.progress,
          message: data.message,
        });

        if (data.status === 'completed') {
          clearInterval(interval);
          await loadResults(sessionId);
        } else if (data.status === 'error') {
          clearInterval(interval);
          showToast(data.message, 'error');
        }
      } catch (error) {
        clearInterval(interval);
        showToast('Status tekshirish xatoligi', 'error');
      }
    }, 1000);
  };

  const loadResults = async (sessionId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/results/${sessionId}`);
      const data = await response.json();
      setResults(data);
      showToast('Tahlil yakunlandi!', 'success');
    } catch (error) {
      showToast('Natijalarni yuklash xatoligi', 'error');
    }
  };

  const downloadResults = async (fileType: 'excel' | 'pdf') => {
    if (!sessionId) {
      showToast('Yuklab olish uchun avval fayl yuklang', 'error');
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/download/${sessionId}/${fileType}`);
      if (response.ok) {
        showToast(`${fileType.toUpperCase()} hisobot yuklab olindi`, 'success');
      } else {
        throw new Error('Yuklab olish xatoligi');
      }
    } catch (error) {
      showToast('Yuklab olish xatoligi', 'error');
    }
  };

  const showSampleResults = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/sample`);
      const data = await response.json();

      if (data.success) {
        setResults(data.results);
        showToast('Namuna natijalar ko\'rsatildi!', 'success');
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      showToast('Namuna natijalar yuklash xatoligi', 'error');
    }
  };

  const renderUploadSection = () => (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>📊 Fayl Yuklash</Text>
      <TouchableOpacity style={styles.uploadButton} onPress={uploadFile}>
        <LinearGradient
          colors={['#667eea', '#764ba2']}
          style={styles.gradientButton}>
          <Icon name="cloud-upload" size={30} color="white" />
          <Text style={styles.buttonText}>Excel fayl tanlash</Text>
        </LinearGradient>
      </TouchableOpacity>

      <TouchableOpacity style={styles.sampleButton} onPress={showSampleResults}>
        <Icon name="visibility" size={20} color="#48bb78" />
        <Text style={styles.sampleButtonText}>Namuna natijalarni ko'rish</Text>
      </TouchableOpacity>
    </View>
  );

  const renderProgressSection = () => (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>🔄 Tahlil Jarayoni</Text>
      <ProgressBar
        progress={processingStatus.progress / 100}
        width={width - 60}
        height={20}
        color="#667eea"
        unfilledColor="#e2e8f0"
        borderWidth={0}
        borderRadius={10}
      />
      <Text style={styles.progressText}>{processingStatus.message}</Text>
    </View>
  );

  const renderResults = () => {
    if (!results) return null;

    return (
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>📈 Tahlil Natijalari</Text>

        {/* Summary Cards */}
        <View style={styles.summaryGrid}>
          <View style={styles.summaryCard}>
            <Text style={styles.summaryTitle}>Talabalar</Text>
            <Text style={styles.summaryValue}>{results.summary.total_students}</Text>
          </View>
          <View style={styles.summaryCard}>
            <Text style={styles.summaryTitle}>Savollar</Text>
            <Text style={styles.summaryValue}>{results.summary.total_questions}</Text>
          </View>
          <View style={styles.summaryCard}>
            <Text style={styles.summaryTitle}>O'rtacha</Text>
            <Text style={styles.summaryValue}>{results.summary.average_score.toFixed(1)}</Text>
          </View>
          <View style={styles.summaryCard}>
            <Text style={styles.summaryTitle}>Eng yuqori</Text>
            <Text style={styles.summaryValue}>{results.summary.highest_score.toFixed(1)}</Text>
          </View>
        </View>

        {/* Grade Distribution */}
        <View style={styles.gradeSection}>
          <Text style={styles.subsectionTitle}>🏆 Baho Taqsimoti</Text>
          <View style={styles.gradeGrid}>
            {Object.entries(results.summary.grade_distribution).map(([grade, count]) => (
              <View key={grade} style={styles.gradeItem}>
                <Text style={styles.gradeText}>{grade}</Text>
                <Text style={styles.gradeCount}>{count}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* Item Difficulties */}
        <View style={styles.itemDifficultiesSection}>
          <Text style={styles.subsectionTitle}>❓ Savol Qiyinliklari</Text>
          {results.item_difficulties.items.slice(0, 10).map((item, index) => (
            <View key={index} style={styles.itemDifficultyItem}>
              <Text style={styles.itemQuestion}>{item.Question}</Text>
              <View style={styles.itemDifficultyInfo}>
                <Text style={styles.itemDifficultyValue}>{item.Difficulty}</Text>
                <View style={[
                  styles.difficultyBadge,
                  item.Difficulty_Level === 'Oson' ? styles.difficultyEasy :
                  item.Difficulty_Level === 'O\'rta' ? styles.difficultyMedium :
                  styles.difficultyHard
                ]}>
                  <Text style={styles.difficultyBadgeText}>{item.Difficulty_Level}</Text>
                </View>
              </View>
            </View>
          ))}
        </View>

        {/* Download Buttons */}
        <View style={styles.downloadSection}>
          <TouchableOpacity
            style={styles.downloadButton}
            onPress={() => downloadResults('excel')}>
            <Icon name="file-download" size={20} color="white" />
            <Text style={styles.downloadButtonText}>Excel hisobot</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.downloadButton}
            onPress={() => downloadResults('pdf')}>
            <Icon name="picture-as-pdf" size={20} color="white" />
            <Text style={styles.downloadButtonText}>PDF hisobot</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#667eea" />
      <LinearGradient colors={['#667eea', '#764ba2']} style={styles.header}>
        <Text style={styles.headerTitle}>Rasch Counter</Text>
        <Text style={styles.headerSubtitle}>Professional Test Analysis</Text>
      </LinearGradient>

      <ScrollView style={styles.content}>
        {renderUploadSection()}

        {processingStatus.status === 'processing' && renderProgressSection()}

        {results && renderResults()}

        {/* Features Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>✨ Xususiyatlar</Text>
          <View style={styles.featuresGrid}>
            <View style={styles.featureItem}>
              <Icon name="psychology" size={30} color="#667eea" />
              <Text style={styles.featureText}>Rasch Model</Text>
            </View>
            <View style={styles.featureItem}>
              <Icon name="assessment" size={30} color="#667eea" />
              <Text style={styles.featureText}>Statistik Tahlil</Text>
            </View>
            <View style={styles.featureItem}>
              <Icon name="emoji-events" size={30} color="#667eea" />
              <Text style={styles.featureText}>UZBMB Standartlari</Text>
            </View>
            <View style={styles.featureItem}>
              <Icon name="file-download" size={30} color="#667eea" />
              <Text style={styles.featureText}>Export Formats</Text>
            </View>
          </View>
        </View>
      </ScrollView>

      <Toast />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9ff',
  },
  header: {
    padding: 30,
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: 'white',
    textShadowColor: 'rgba(0,0,0,0.3)',
    textShadowOffset: {width: 2, height: 2},
    textShadowRadius: 4,
  },
  headerSubtitle: {
    fontSize: 16,
    color: 'white',
    opacity: 0.9,
    marginTop: 5,
  },
  content: {
    flex: 1,
    padding: 20,
  },
  section: {
    backgroundColor: 'white',
    borderRadius: 15,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 5,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#667eea',
    marginBottom: 15,
  },
  subsectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#4a5568',
    marginBottom: 10,
  },
  uploadButton: {
    marginBottom: 15,
  },
  gradientButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
    borderRadius: 25,
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 10,
  },
  sampleButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 15,
    backgroundColor: '#f0fff4',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#48bb78',
  },
  sampleButtonText: {
    color: '#48bb78',
    fontSize: 14,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  progressText: {
    textAlign: 'center',
    marginTop: 10,
    fontSize: 14,
    color: '#4a5568',
    fontWeight: 'bold',
  },
  summaryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  summaryCard: {
    backgroundColor: '#f8f9ff',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    width: (width - 80) / 2,
    marginBottom: 10,
    borderLeftWidth: 4,
    borderLeftColor: '#667eea',
  },
  summaryTitle: {
    fontSize: 12,
    color: '#666',
    marginBottom: 5,
  },
  summaryValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#667eea',
  },
  gradeSection: {
    marginBottom: 20,
  },
  gradeGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  gradeItem: {
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    width: (width - 80) / 4,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 1},
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  gradeText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#667eea',
  },
  gradeCount: {
    fontSize: 12,
    color: '#666',
    marginTop: 5,
  },
  itemDifficultiesSection: {
    marginBottom: 20,
  },
  itemDifficultyItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 15,
    backgroundColor: '#f8f9ff',
    borderRadius: 10,
    marginBottom: 10,
  },
  itemQuestion: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#2d3748',
    flex: 1,
  },
  itemDifficultyInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  itemDifficultyValue: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#667eea',
    marginRight: 10,
  },
  difficultyBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  difficultyEasy: {
    backgroundColor: '#c6f6d5',
  },
  difficultyMedium: {
    backgroundColor: '#fef5e7',
  },
  difficultyHard: {
    backgroundColor: '#fed7d7',
  },
  difficultyBadgeText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#2d3748',
  },
  downloadSection: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 20,
  },
  downloadButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#667eea',
    padding: 15,
    borderRadius: 20,
    flex: 0.45,
    justifyContent: 'center',
  },
  downloadButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  featuresGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  featureItem: {
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#f8f9ff',
    borderRadius: 10,
    width: (width - 80) / 2,
    marginBottom: 15,
  },
  featureText: {
    fontSize: 12,
    color: '#4a5568',
    marginTop: 10,
    textAlign: 'center',
  },
});

export default App;
