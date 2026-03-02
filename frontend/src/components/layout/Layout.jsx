import Sidebar from './Sidebar';
import Navbar from './Navbar';

export default function Layout({ children }) {
    return (
        <div className="app-layout">
            <Sidebar />
            <div className="main-content">
                <Navbar />
                <main className="page-container fade-in">
                    {children}
                </main>
            </div>
        </div>
    );
}
