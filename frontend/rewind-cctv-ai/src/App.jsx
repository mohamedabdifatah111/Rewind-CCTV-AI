import { Link, Route, Routes } from 'react-router-dom';
import AppLayout from './layouts/AppLayout.jsx';
import Overview from './pages/Overview.jsx';
import UploadPage from './pages/UploadPage.jsx';
import LibraryPage from './pages/LibraryPage.jsx';
import VideoDetailsPage from './pages/VideoDetailsPage.jsx';
import SearchPage from './pages/SearchPage.jsx';
import HistoryPage from './pages/HistoryPage.jsx';
import SettingsPage from './pages/SettingsPage.jsx';

const NotFound = () => <div className="py-20 text-center"><h1 className="text-xl font-semibold">Page not found</h1><Link to="/" className="btn mt-4 inline-flex">Back to overview</Link></div>;

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Overview />} />
        <Route path="upload" element={<UploadPage />} />
        <Route path="library" element={<LibraryPage />} />
        <Route path="library/:id" element={<VideoDetailsPage />} />
        <Route path="search" element={<SearchPage />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
