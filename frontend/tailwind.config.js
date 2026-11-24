/** Hệ màu "bản vẽ kỹ thuật": xanh mực in bản vẽ + vàng an toàn công trường (gợi chất Đại học Xây Dựng). */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: { DEFAULT: '#1F3A5F', 50: '#EEF2F7', 100: '#D9E2EE', 600: '#284B78', 700: '#1F3A5F', 900: '#14263F' },
        amber: { DEFAULT: '#E8A33D', 50: '#FDF5E7', 100: '#FAE6C2', 600: '#C9852A' },
        paper: '#F4F6F9',
        line: '#DDE3EA',
        text: '#17212B',
        muted: '#66737F',
        danger: '#C2413A',
        success: '#2F855A',
      },
      fontFamily: { sans: ['"Be Vietnam Pro"', 'system-ui', 'Segoe UI', 'Roboto', 'sans-serif'] },
      borderRadius: { card: '14px' },
      boxShadow: { card: '0 1px 2px rgba(23,33,43,0.06), 0 0 0 1px rgba(23,33,43,0.04)' },
    },
  },
  plugins: [],
};
