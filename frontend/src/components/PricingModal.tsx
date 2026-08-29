import React from 'react';
import { X, Check, Zap, Sparkles, Shield, Rocket } from 'lucide-react';
import { UserCredits } from '../types';

interface PricingModalProps {
  isOpen: boolean;
  onClose: () => void;
  credits: UserCredits | null;
  onUpgradeTier: (tier: string) => void;
}

export const PricingModal: React.FC<PricingModalProps> = ({ isOpen, onClose, credits, onUpgradeTier }) => {
  if (!isOpen || !credits) return null;

  const tiers = [
    {
      key: 'FREE',
      name: 'Gói Miễn Phí (FREE)',
      price: '0đ',
      period: 'mãi mãi',
      desc: 'Dành cho người mới bắt đầu trải nghiệm sức mạnh của AI Video',
      icon: Zap,
      color: 'slate',
      badge: 'Cơ bản',
      popular: false
    },
    {
      key: 'PRO',
      name: 'Pro Sáng Tạo (PRO)',
      price: '99.000đ',
      period: '/tháng',
      desc: 'Phù hợp cho cá nhân làm video ngắn và dịch thuật nội dung',
      icon: Sparkles,
      color: 'indigo',
      badge: 'Tiết kiệm',
      popular: false
    },
    {
      key: 'PRO_PLUS',
      name: 'Chuyên Nghiệp (PRO+)',
      price: '199.000đ',
      period: '/tháng',
      desc: 'Gói tối ưu nhất cho Creator, Podcaster, Reup & MMO tự động',
      icon: Rocket,
      color: 'purple',
      badge: 'Khuyên Dùng 🔥',
      popular: true
    },
    {
      key: 'BUSINESS',
      name: 'Doanh Nghiệp (BUSINESS)',
      price: '499.000đ',
      period: '/tháng',
      desc: 'Cho Agency, Studio & Team cần xử lý video hàng loạt tốc độ cao',
      icon: Shield,
      color: 'pink',
      badge: 'Doanh Nghiệp',
      popular: false
    }
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md overflow-y-auto">
      <div className="bg-[#0f1422] border border-slate-800 rounded-3xl max-w-5xl w-full p-6 sm:p-10 shadow-2xl relative my-8">
        
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-6 right-6 p-2 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="text-center max-w-2xl mx-auto mb-10">
          <span className="text-xs uppercase font-extrabold tracking-wider bg-purple-500/20 text-purple-300 border border-purple-500/30 px-3 py-1 rounded-full">
            BẢNG GIÁ & HẠN MỨC CREDIT
          </span>
          <h2 className="text-2xl sm:text-3xl font-black text-white mt-3">
            Nâng Tầm Tốc Độ Sản Xuất Video Bằng AI
          </h2>
          <p className="text-sm text-slate-400 mt-2">
            Mở khóa toàn bộ tính năng Lồng Tiếng Đa Vai, Căn Timing Tự Động, Cắt Shorts 9:16 & Nhân Bản 10x Content.
          </p>
        </div>

        {/* Pricing Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {tiers.map((t) => {
            const isCurrent = credits.current_tier === t.key;
            const tierData = credits.all_tiers[t.key] as any || {};
            const features = tierData.features || [];

            return (
              <div
                key={t.key}
                className={`rounded-2xl p-5 flex flex-col justify-between transition-all relative ${
                  t.popular
                    ? 'bg-gradient-to-b from-purple-950/40 via-slate-900 to-slate-900 border-2 border-purple-500 shadow-2xl shadow-purple-500/20 scale-[1.02]'
                    : 'bg-slate-900/60 border border-slate-800 hover:border-slate-700'
                }`}
              >
                {t.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-[10px] font-black uppercase tracking-wider px-3 py-0.5 rounded-full shadow-md">
                    {t.badge}
                  </div>
                )}

                <div>
                  <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                    {t.name}
                  </div>
                  <div className="flex items-baseline gap-1 mb-1">
                    <span className="text-2xl font-black text-white">{t.price}</span>
                    <span className="text-xs text-slate-400">{t.period}</span>
                  </div>
                  <p className="text-[11px] text-slate-400 mb-5 min-h-[32px]">{t.desc}</p>

                  <div className="space-y-2.5 border-t border-slate-800/80 pt-4 mb-6">
                    {features.map((feat: string, fIdx: number) => (
                      <div key={fIdx} className="flex items-start gap-2 text-xs text-slate-300">
                        <Check className="w-3.5 h-3.5 text-purple-400 flex-shrink-0 mt-0.5" />
                        <span>{feat}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <button
                  onClick={() => {
                    onUpgradeTier(t.key);
                    onClose();
                  }}
                  disabled={isCurrent}
                  className={`w-full py-2.5 rounded-xl font-bold text-xs transition-all ${
                    isCurrent
                      ? 'bg-slate-800 text-slate-400 border border-slate-700 cursor-default'
                      : t.popular
                      ? 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white shadow-lg shadow-purple-600/30'
                      : 'bg-slate-800 hover:bg-slate-700 text-white border border-slate-700'
                  }`}
                >
                  {isCurrent ? 'Gói Hiện Tại Của Bạn' : 'Chọn Gói Này'}
                </button>

              </div>
            );
          })}
        </div>

        {/* Footer info */}
        <div className="text-center text-xs text-slate-500 mt-8">
          🔒 Thanh toán an toàn qua QR Chuyển Khoản / Thẻ / MoMo • Hỗ trợ xuất hóa đơn VAT cho doanh nghiệp
        </div>

      </div>
    </div>
  );
};
