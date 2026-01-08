import React, { useEffect, useMemo, useRef, useState, useCallback } from 'react';
import { CaretLeft, CaretRight, WarningCircle, Flask, Check, X, ArrowCounterClockwise, CheckCircle, XCircle, Warning, Eye, Spinner, BookOpen, Brain, ListChecks, PlayCircle, MagnifyingGlass, Books, CaretDown, Gear, Exam, Download, Upload, FloppyDisk } from '@phosphor-icons/react';
import { KEY_POINTS_DB } from './keyPointsData';
import cardData from './data.json';
import nonMedData from './非药化专业.json';
import './index.css';

// --- JSME Loader (CDN Only for Reliability) ---
// Note: Offline GWT files are complex to scrape. We default to online CDN.
const ensureJsmeReady = (() => {
  let promise;
  return () => {
    if (promise) return promise;
    promise = new Promise((resolve, reject) => {
      if (window.JSApplet && window.JSApplet.JSME) { resolve(); return; }

      const prev = window.jsmeOnLoad;
      window.jsmeOnLoad = function () { try { prev && prev(); } catch (_) { } resolve(); };

      if (!document.getElementById("jsme-script")) {
        const s = document.createElement("script");
        s.id = "jsme-script";
        s.src = "/libs/jsme/jsme.nocache.js";
        s.async = true;
        s.onerror = () => {
          console.error("Failed to load JSME from CDN.");
          // Could add a retry or alert here
        };
        document.body.appendChild(s);
      }

      let tries = 0;
      const timer = setInterval(() => {
        tries++;
        if (window.JSApplet && window.JSApplet.JSME) { clearInterval(timer); resolve(); }
        if (tries > 100) { clearInterval(timer); reject(new Error("JSME init timeout - Check Internet Connection")); }
      }, 200);
    });
    return promise;
  };
})();

// --- Component: JSME Editor ---
function JSMEEditor({ id, onReady, onSmilesChange }) {
  const containerRef = useRef(null);
  useEffect(() => {
    let cancelled = false;
    ensureJsmeReady().then(() => {
      if (cancelled || !containerRef.current) return;
      const applet = new window.JSApplet.JSME(id, "100%", "100%", { options: "newlook,star" });
      onReady && onReady(applet);
      try {
        applet.setCallBack("AfterStructureModified", () => {
          onSmilesChange && onSmilesChange(applet.smiles());
        });
      } catch (e) { console.warn("JSME Callback error", e); }
    }).catch(e => {
      console.error(e);
      if (containerRef.current) containerRef.current.innerHTML = "<div class='flex items-center justify-center h-full text-red-400 p-4 text-center text-sm'>Could not load editor.<br>Check connection.</div>";
    });
    return () => { cancelled = true; if (containerRef.current) containerRef.current.innerHTML = ""; };
  }, [id]);
  return <div id={id} ref={containerRef} className="w-full h-full rounded-lg overflow-hidden bg-white" />;
}

// --- Helper: Data Generation ---
const generateOptions = (correctCard, allCards, count = 3) => {
  // 1. Prioritize Same Chapter
  let candidates = allCards.filter(c => c.chapter === correctCard.chapter && c.id !== correctCard.id);
  // 2. Fallback to others
  if (candidates.length < count) {
    const others = allCards.filter(c => c.chapter !== correctCard.chapter && c.id !== correctCard.id);
    const shuffledOthers = others.sort(() => Math.random() - 0.5);
    candidates = [...candidates, ...shuffledOthers];
  }
  // 3. Shuffle & Slice
  const distractors = candidates.sort(() => Math.random() - 0.5).slice(0, count);
  return [correctCard, ...distractors].sort(() => Math.random() - 0.5);
};

// --- Helper: Batch Generation ---
const generateLearningBatch = (allCards, progress, orderMode = 'sequential', batchSize = 15) => {
  const newCards = [];
  const activeCards = [];

  // 1. Classify
  allCards.forEach(card => {
    const p = progress[card.id];
    const status = p?.status || 'learning';

    // Skip mastered
    if (status === 'mastered') return;

    const stage = p?.learningStage || 0;
    // Inject stage info
    const cardWithStage = { ...card, learningStage: stage, reviewTempStage: p?.reviewTempStage };

    if (stage > 0) {
      activeCards.push(cardWithStage);
    } else {
      newCards.push(cardWithStage);
    }
  });

  // 2. Sort New Cards
  if (orderMode === 'random') {
    newCards.sort(() => Math.random() - 0.5);
  } else {
    // Sequential: Maintain original array order (assumed to be Chapter order)
  }

  // 3. Create Batch (Limit New Cards)
  const batchNew = newCards.slice(0, batchSize);

  // Mix Active Cards (Shuffle them)
  activeCards.sort(() => Math.random() - 0.5);

  // 4. Interleave
  // Strategy: Insert 1 active card after every 2-3 new cards
  const queue = [];
  let newIdx = 0;
  let activeIdx = 0;

  while (newIdx < batchNew.length || activeIdx < activeCards.length) {
    // Add 2-3 new cards
    const chunk = Math.floor(Math.random() * 2) + 2;
    for (let i = 0; i < chunk && newIdx < batchNew.length; i++) {
      queue.push(batchNew[newIdx++]);
    }
    // Add 1-2 active cards (if any)
    const activeChunk = Math.floor(Math.random() * 2) + 1;
    for (let i = 0; i < activeChunk && activeIdx < activeCards.length; i++) {
      queue.push(activeCards[activeIdx++]);
    }
    // Logic breaker: prevent infinite loop if one pool is empty
    if (newIdx >= batchNew.length && activeIdx < activeCards.length) {
      queue.push(...activeCards.slice(activeIdx));
      break;
    }
  }

  return queue;
};

const getEfficacyDescription = (card) => {
  const points = KEY_POINTS_DB[card.en] || KEY_POINTS_DB[card.cn];
  if (points) {
    const clinical = points.find(p => p.startsWith("【临床】") || p.startsWith("【作用】"));
    if (clinical) return clinical.replace(/【.*?】/, '').trim();
    const first = points[0];
    if (first && !first.startsWith("【结构】")) return first.replace(/【.*?】/, '').trim();
  }
  return `${card.chapter.split(" ")[1]}药物`;
};

const generateEfficacyOptions = (correctCard, allCards, count = 4) => {
  const correctDesc = getEfficacyDescription(correctCard);
  const candidates = allCards.filter(c => {
    if (c.id === correctCard.id) return false;
    const desc = getEfficacyDescription(c);
    return desc !== correctDesc && desc.length > 5;
  });

  const distractors = candidates.sort(() => Math.random() - 0.5).slice(0, count).map(c => getEfficacyDescription(c));
  return [correctDesc, ...distractors].sort(() => Math.random() - 0.5);
};



// --- Component: Data Management Modal ---
function DataManagementModal({ isOpen, onClose, onImport, onExport }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-3xl shadow-2xl max-w-md w-full overflow-hidden" onClick={e => e.stopPropagation()}>
        <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50">
          <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            <Gear weight="fill" className="text-slate-500" /> 数据管理
          </h2>
          <button onClick={onClose} className="p-2 hover:bg-slate-200 rounded-full transition text-slate-500">
            <X size={20} />
          </button>
        </div>

        <div className="p-8 space-y-6">
          {/* Export */}
          <div className="bg-indigo-50 rounded-2xl p-6 border border-indigo-100 hover:shadow-md transition">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-indigo-100 text-indigo-600 rounded-xl">
                <Download size={24} weight="bold" />
              </div>
              <div className="flex-1">
                <h3 className="font-bold text-slate-800 mb-1">导出进度备份</h3>
                <p className="text-sm text-slate-500 mb-4">将您的学习进度、禁用药物列表等数据导出为文件，以便备份或迁移。</p>
                <button
                  onClick={onExport}
                  className="px-4 py-2 bg-indigo-600 text-white text-sm font-bold rounded-lg hover:bg-indigo-700 transition shadow-lg shadow-indigo-200 flex items-center gap-2"
                >
                  <FloppyDisk weight="fill" /> 立即导出
                </button>
              </div>
            </div>
          </div>

          {/* Import */}
          <div className="bg-amber-50 rounded-2xl p-6 border border-amber-100 hover:shadow-md transition">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-amber-100 text-amber-600 rounded-xl">
                <Upload size={24} weight="bold" />
              </div>
              <div className="flex-1">
                <h3 className="font-bold text-slate-800 mb-1">导入数据恢复</h3>
                <p className="text-sm text-slate-500 mb-4">从备份文件恢复数据。<br /><span className="text-rose-500 font-bold">注意：当前进度将被覆盖！</span></p>
                <label className="px-4 py-2 bg-amber-500 text-white text-sm font-bold rounded-lg hover:bg-amber-600 transition shadow-lg shadow-amber-200 flex items-center gap-2 w-fit cursor-pointer">
                  <Upload weight="fill" /> 选择文件导入
                  <input
                    type="file"
                    accept=".json"
                    onChange={onImport}
                    className="hidden"
                  />
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// --- Component: MainMenu ---
function MainMenu({ onSelectMode, stats, currentMajor, onSwitchMajor, chapters, realisticMode, onToggleRealisticMode, onOpenSettings }) {
  const [isRandom, setIsRandom] = useState(false);
  const [selectedChapter, setSelectedChapter] = useState('all');
  const [showChapterDropdown, setShowChapterDropdown] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-100 flex flex-col items-center justify-center p-6">
      {/* Realistic Mode Toggle - Top Left */}
      <div className="absolute top-6 left-6">
        <button
          onClick={onToggleRealisticMode}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all border shadow-sm ${realisticMode
            ? 'bg-amber-500 text-white border-amber-600 shadow-amber-200'
            : 'bg-white/50 backdrop-blur-sm text-slate-500 border-slate-200 hover:text-amber-600 hover:border-amber-300'
            }`}
        >
          <Exam size={20} weight={realisticMode ? 'fill' : 'regular'} />
          <span>{realisticMode ? '拟真模式 ON' : '拟真模式'}</span>
        </button>
        {realisticMode && (
          <div className="mt-2 text-xs text-amber-600 bg-amber-50 px-3 py-1.5 rounded-lg border border-amber-200">
            ✓ 黑白图像 + 随机旋转
          </div>
        )}
      </div>



      {/* Settings Button */}
      <div className="absolute top-6 right-6 flex items-center gap-3">
        <div className="flex bg-white/50 backdrop-blur-sm p-1 rounded-xl border border-slate-200 shadow-sm">
          <button
            onClick={() => onSwitchMajor('med')}
            className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${currentMajor === 'med' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-500 hover:text-indigo-600'}`}
          >
            药化专业
          </button>
          <button
            onClick={() => onSwitchMajor('non-med')}
            className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${currentMajor === 'non-med' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-500 hover:text-indigo-600'}`}
          >
            非药化专业
          </button>
        </div>

        <button
          onClick={onOpenSettings}
          className="p-3 bg-white/50 backdrop-blur-sm rounded-xl border border-slate-200 shadow-sm text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 transition"
          title="数据管理"
        >
          <Gear size={24} weight="fill" />
        </button>
      </div>

      <div className="text-center mb-10">
        <div className="w-20 h-20 bg-indigo-600 rounded-2xl flex items-center justify-center text-white mx-auto mb-4 shadow-xl rotate-3">
          <Flask size={48} weight="duotone" />
        </div>
        <h1 className="text-4xl font-extrabold text-slate-800 mb-2 tracking-tight">药化智能卡片 <span className="text-indigo-600 text-lg px-2 py-1 bg-indigo-100 rounded-lg align-top ml-2">Pro</span></h1>
        <p className="text-slate-500">智能间隔重复 · 深度记忆强化</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 max-w-7xl w-full">
        {/* 顺序学习 - 带章节选择 */}
        <div className="group bg-white p-8 rounded-3xl shadow-lg hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 border border-slate-100 text-left relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-blue-50 rounded-full -mr-10 -mt-10 group-hover:scale-150 transition-transform duration-500"></div>
          <div className="relative z-10 w-full">
            <div className="w-14 h-14 bg-blue-100 text-blue-600 rounded-2xl flex items-center justify-center mb-6 text-2xl group-hover:rotate-12 transition-transform">
              <PlayCircle weight="fill" />
            </div>
            <h3 className="text-xl font-bold text-slate-800 mb-2">顺序学习</h3>
            <p className="text-slate-500 text-sm mb-4">循序渐进的记忆流程：<br />辨识 → 熟悉 → 疗效 → 掌握</p>

            {/* 章节选择器 */}
            <div className="relative mb-4">
              <button
                onClick={(e) => { e.stopPropagation(); setShowChapterDropdown(!showChapterDropdown); }}
                className="w-full flex items-center justify-between px-3 py-2 bg-slate-50 hover:bg-slate-100 rounded-lg text-sm text-slate-600 border border-slate-200 transition"
              >
                <span className="truncate">{selectedChapter === 'all' ? '📚 全部章节' : selectedChapter.split(' ')[0]}</span>
                <CaretDown size={16} className={`transition-transform ${showChapterDropdown ? 'rotate-180' : ''}`} />
              </button>
              {showChapterDropdown && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-xl z-50 max-h-48 overflow-y-auto">
                  <button
                    onClick={(e) => { e.stopPropagation(); setSelectedChapter('all'); setShowChapterDropdown(false); }}
                    className={`w-full text-left px-3 py-2 text-sm hover:bg-indigo-50 ${selectedChapter === 'all' ? 'bg-indigo-100 text-indigo-700 font-bold' : 'text-slate-600'}`}
                  >
                    📚 全部章节
                  </button>
                  {chapters.map(ch => (
                    <button
                      key={ch}
                      onClick={(e) => { e.stopPropagation(); setSelectedChapter(ch); setShowChapterDropdown(false); }}
                      className={`w-full text-left px-3 py-2 text-sm hover:bg-indigo-50 ${selectedChapter === ch ? 'bg-indigo-100 text-indigo-700 font-bold' : 'text-slate-600'}`}
                    >
                      {ch.split(' ')[0]}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-bold text-blue-600 bg-blue-50 px-3 py-1.5 rounded-full w-fit">
                待学: {stats.learningCount}
              </div>
              <div
                onClick={(e) => { e.stopPropagation(); setIsRandom(!isRandom); }}
                className={`flex items-center gap-1 px-2 py-1 rounded-full cursor-pointer transition-colors text-xs ${isRandom ? 'bg-indigo-100 text-indigo-700' : 'bg-slate-100 text-slate-500'}`}
              >
                <ArrowCounterClockwise size={12} className={isRandom ? 'rotate-180 transition-transform' : ''} />
                <span className="font-bold">{isRandom ? "乱序" : "顺序"}</span>
              </div>
            </div>

            <button
              onClick={() => onSelectMode('learning', isRandom ? 'random' : 'sequential', selectedChapter)}
              className="w-full mt-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl transition shadow-lg shadow-blue-200"
            >
              开始学习
            </button>
          </div>
        </div>

        {/* 深度复习 */}
        <button
          onClick={() => onSelectMode('review')}
          className="group bg-white p-8 rounded-3xl shadow-lg hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 border border-slate-100 text-left relative overflow-hidden"
        >
          <div className="absolute top-0 right-0 w-32 h-32 bg-purple-50 rounded-full -mr-10 -mt-10 group-hover:scale-150 transition-transform duration-500"></div>
          <div className="relative z-10">
            <div className="w-14 h-14 bg-purple-100 text-purple-600 rounded-2xl flex items-center justify-center mb-6 text-2xl group-hover:rotate-12 transition-transform">
              <Brain weight="fill" />
            </div>
            <h3 className="text-xl font-bold text-slate-800 mb-2">深度复习</h3>
            <p className="text-slate-500 text-sm mb-4">针对已掌握药物的强化复习<br />包含内部重学循环</p>
            <div className="flex items-center gap-2 text-xs font-bold text-purple-600 bg-purple-50 px-3 py-1.5 rounded-full w-fit">
              待复习: {stats.reviewCount}
            </div>
          </div>
        </button>

        {/* 药物目录 - 新增 */}
        <button
          onClick={() => onSelectMode('catalog')}
          className="group bg-white p-8 rounded-3xl shadow-lg hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 border border-slate-100 text-left relative overflow-hidden"
        >
          <div className="absolute top-0 right-0 w-32 h-32 bg-amber-50 rounded-full -mr-10 -mt-10 group-hover:scale-150 transition-transform duration-500"></div>
          <div className="relative z-10">
            <div className="w-14 h-14 bg-amber-100 text-amber-600 rounded-2xl flex items-center justify-center mb-6 text-2xl group-hover:rotate-12 transition-transform">
              <Books weight="fill" />
            </div>
            <h3 className="text-xl font-bold text-slate-800 mb-2">药物目录</h3>
            <p className="text-slate-500 text-sm mb-4">按章节浏览全部药物<br />支持搜索和快速查看详情</p>
            <div className="flex items-center gap-2 text-xs font-bold text-amber-600 bg-amber-50 px-3 py-1.5 rounded-full w-fit">
              <MagnifyingGlass size={14} /> 搜索浏览
            </div>
          </div>
        </button>

        {/* 经典模式 */}
        <button
          onClick={() => onSelectMode('card')}
          className="group bg-white p-8 rounded-3xl shadow-lg hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 border border-slate-100 text-left relative overflow-hidden"
        >
          <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-50 rounded-full -mr-10 -mt-10 group-hover:scale-150 transition-transform duration-500"></div>
          <div className="relative z-10">
            <div className="w-14 h-14 bg-emerald-100 text-emerald-600 rounded-2xl flex items-center justify-center mb-6 text-2xl group-hover:rotate-12 transition-transform">
              <ListChecks weight="fill" />
            </div>
            <h3 className="text-xl font-bold text-slate-800 mb-2">经典模式</h3>
            <p className="text-slate-500 text-sm mb-4">传统的卡片浏览模式<br />支持特定章节和筛选</p>
          </div>
        </button>

        {/* 模拟考试 */}
        <button
          onClick={() => onSelectMode('exam')}
          className="group bg-white p-8 rounded-3xl shadow-lg hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 border border-slate-100 text-left relative overflow-hidden"
        >
          <div className="absolute top-0 right-0 w-32 h-32 bg-rose-50 rounded-full -mr-10 -mt-10 group-hover:scale-150 transition-transform duration-500"></div>
          <div className="relative z-10">
            <div className="w-14 h-14 bg-gradient-to-br from-rose-100 to-purple-100 text-rose-600 rounded-2xl flex items-center justify-center mb-6 text-2xl group-hover:rotate-12 transition-transform">
              <Exam weight="fill" />
            </div>
            <h3 className="text-xl font-bold text-slate-800 mb-2">模拟考试</h3>
            <p className="text-slate-500 text-sm mb-4">选择章节进行模拟测试<br />写药名 + 写结构</p>
            <div className="flex items-center gap-2 text-xs font-bold text-rose-600 bg-rose-50 px-3 py-1.5 rounded-full w-fit">
              📝 考试模式
            </div>
          </div>
        </button>
      </div>
    </div >
  );
}



// --- Component: Quiz View ---
function QuizView({ card, mode, onAnswer, options, onNext, progress, getImagePath, imageRotation = 0 }) {
  const [selected, setSelected] = useState(null);
  const [answered, setAnswered] = useState(false);
  const [hoveredOption, setHoveredOption] = useState(null);

  // Keyboard shortcut for Next
  useEffect(() => {
    const handleKey = (e) => {
      if (answered && (e.code === 'Space' || e.code === 'Enter')) {
        onNext();
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [answered, onNext]);

  useEffect(() => {
    setSelected(null);
    setAnswered(false);
    setHoveredOption(null);
  }, [card, mode]);

  const handleSelect = (option) => {
    if (selected || answered) return;
    setSelected(option);
    setAnswered(true);

    const isCorrect = mode === 'identify-name'
      ? option.id === card.id
      : option.id === card.id;

    onAnswer(isCorrect);
  };

  // Determine displayed content (Hovered -> Correct Card)
  const displayCard = hoveredOption || card;

  return (
    <div className="flex flex-col items-center max-w-5xl w-full mx-auto p-4 flex-grow justify-start">
      {/* Progress Bar */}
      <div className="w-full max-w-xl mb-4 flex gap-1">
        {[0, 1, 2, 3].map(lvl => (
          <div key={lvl} className={`h-1.5 flex-1 rounded-full ${progress >= lvl ? 'bg-indigo-500' : 'bg-slate-200'}`} />
        ))}
      </div>

      <div className="flex w-full gap-6 flex-col md:flex-row items-stretch">
        {/* Left: Feedback Panel - shows question before answering, details after */}
        <div className="w-full md:w-1/2 bg-white rounded-3xl shadow-xl overflow-hidden border border-slate-100 p-6 flex flex-col items-center min-h-[400px] justify-center">
          {/* Before answering: show the QUESTION, hide the ANSWER */}
          {!answered ? (
            <>
              {mode === 'identify-name' ? (
                // 看结构选药名：显示结构，隐藏药名
                <>
                  <div className="w-full h-56 flex items-center justify-center p-4 bg-slate-50 rounded-2xl mb-4">
                    <img src={getImagePath ? getImagePath(card.image, imageRotation) : card.image} alt="Structure" className="max-w-full max-h-full object-contain" />
                  </div>
                  <h3 className="text-center text-slate-500 font-medium">请根据上方结构选择正确的药物名称</h3>
                </>
              ) : (
                // 看药名选结构：显示药名，隐藏结构
                <>
                  <h2 className="text-3xl font-bold text-slate-800 mb-2">{card.cn}</h2>
                  <p className="text-slate-400 text-lg mb-6">{card.en}</p>
                  <h3 className="text-center text-slate-500 font-medium">请根据药物名称选择正确的结构</h3>
                </>
              )}
            </>
          ) : (
            // After answering: show full details for hovered/correct card
            <>
              <div className="w-full h-56 flex items-center justify-center p-4 bg-slate-50 rounded-2xl mb-4 relative">
                <img src={getImagePath ? getImagePath(displayCard.image, imageRotation) : displayCard.image} alt="Structure" className="max-w-full max-h-full object-contain" />
                {hoveredOption && hoveredOption.id !== card.id && (
                  <div className="absolute top-2 right-2 bg-rose-500 text-white text-xs px-2 py-1 rounded">干扰项</div>
                )}
              </div>
              <h2 className="text-xl font-bold text-slate-800 mb-1">{displayCard.cn}</h2>
              <p className="text-slate-400 text-sm mb-4">{displayCard.en}</p>
              <div className="text-left w-full bg-slate-50 p-4 rounded-xl text-sm text-slate-600 overflow-y-auto max-h-32">
                {getEfficacyDescription(displayCard)}
                <div className="mt-2 text-xs text-slate-400">将鼠标悬停在选项上查看其他药物详情</div>
              </div>
            </>
          )}
        </div>

        {/* Right: Options Area */}
        <div className="w-full md:w-1/2 flex flex-col gap-3">
          <div className={`grid gap-3 ${mode === 'identify-structure' ? 'grid-cols-2' : 'grid-cols-1'}`}>
            {options.map((opt, idx) => {
              const isSelected = selected?.id === opt.id;
              const isCorrect = opt.id === card.id;

              // Style Logic
              let styleClass = "bg-white border-slate-200 hover:border-indigo-300 hover:bg-indigo-50";
              if (answered) {
                if (isCorrect) styleClass = "bg-emerald-50 border-emerald-500 ring-1 ring-emerald-500";
                else if (isSelected) styleClass = "bg-rose-50 border-rose-500 ring-1 ring-rose-500";
                else styleClass = "opacity-60 bg-slate-50 border-slate-200";
              }

              return (
                <button
                  key={idx}
                  onClick={() => handleSelect(opt)}
                  onMouseEnter={() => answered && setHoveredOption(opt)}
                  onMouseLeave={() => answered && setHoveredOption(null)}
                  className={`relative p-4 rounded-xl text-left transition-all border-2 flex flex-col items-center justify-center gap-2 cursor-pointer ${styleClass}`}
                >
                  {mode === 'identify-name' ? (
                    <span className={`text-lg font-bold ${answered && isCorrect ? 'text-emerald-700' : 'text-slate-700'}`}>{opt.cn}</span>
                  ) : (
                    <>
                      <div className="w-full h-32 flex items-center justify-center">
                        <img src={getImagePath ? getImagePath(opt.image, imageRotation) : opt.image} className="max-w-full max-h-full object-contain" alt="" />
                      </div>
                      {answered && (
                        <div className="text-xs font-bold text-slate-500 mt-1">{opt.cn}</div>
                      )}
                    </>
                  )}

                  {answered && isCorrect && (
                    <div className="absolute top-2 right-2 text-emerald-500"><CheckCircle weight="fill" size={24} /></div>
                  )}
                  {answered && isSelected && !isCorrect && (
                    <div className="absolute top-2 right-2 text-rose-500"><XCircle weight="fill" size={24} /></div>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Manual Next Button */}
      {answered && (
        <button
          onClick={onNext}
          className="w-full max-w-md py-4 rounded-2xl bg-indigo-600 text-white font-bold text-lg shadow-xl shadow-indigo-200 hover:bg-indigo-700 hover:scale-[1.02] transition-all animate-in fade-in slide-in-from-bottom-4"
        >
          下一页 (Space) <CaretRight className="inline ml-1" weight="bold" />
        </button>
      )}
    </div>
  );
}

// --- Component: Learning Flow ---
// --- Component: Learning Flow ---
function LearningFlow({ cards: initialCards, onExit, updateProgress, initialReviewMode = false, getImagePath, realisticMode }) {
  const [cards, setCards] = useState(initialCards);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [currentCard, setCurrentCard] = useState(initialCards[0]);
  // 初始化 tempStage 为第一张卡片的阶段，而不是 null
  const [tempStage, setTempStage] = useState(() => {
    const firstCard = initialCards[0];
    if (!firstCard) return 0;
    return firstCard.reviewTempStage ?? firstCard.learningStage ?? 0;
  });
  const [quizOptions, setQuizOptions] = useState(() => {
    // 如果初始阶段是 0 或 2，需要预先生成选项
    const firstCard = initialCards[0];
    const stage = firstCard?.reviewTempStage ?? firstCard?.learningStage ?? 0;
    if (stage === 0 || stage === 2) {
      return generateOptions(firstCard, initialCards.concat(cardData), 3);
    }
    return [];
  });
  const [showInterimDetails, setShowInterimDetails] = useState(false);
  const [lastQuizResult, setLastQuizResult] = useState(null);
  const [imageRotation, setImageRotation] = useState(() => {
    if (realisticMode) {
      const rotations = [0, 90, 180, 270];
      return rotations[Math.floor(Math.random() * rotations.length)];
    }
    return 0;
  });

  // Generate new random rotation when card changes (for realistic mode)
  useEffect(() => {
    if (realisticMode) {
      const rotations = [0, 90, 180, 270];
      setImageRotation(rotations[Math.floor(Math.random() * rotations.length)]);
    } else {
      setImageRotation(0);
    }
  }, [currentIndex, realisticMode]);

  useEffect(() => {
    if (!cards[currentIndex]) return;
    const card = cards[currentIndex];
    setCurrentCard(card);
    const stage = card.reviewTempStage ?? card.learningStage ?? 0;
    setTempStage(stage);

    if (stage === 0) {
      // Stage 0: Identify Name
      setQuizOptions(generateOptions(card, cards.concat(cardData), 3));
    } else if (stage === 2) {
      // Stage 2: Identify Structure (from Name)
      setQuizOptions(generateOptions(card, cards.concat(cardData), 3));
    }
  }, [currentIndex, cards]);

  const handleNext = () => {
    if (currentIndex < cards.length - 1) {
      setCurrentIndex(prev => prev + 1);
    } else {
      // Check if there are any cards left that are not mastered in this batch?
      // Actually, the queue logic ensures we only finish when we fall off the end.
      // But let's verify if we should just loop? 
      // No, the re-insertion logic handles the loop. If we reach the end, it means everything before is done or pushed back.
      alert("🎉 本组学习完成！休息一下吧！");
      onExit();
    }
  };

  const onQuizAnswer = (isCorrect) => {
    setLastQuizResult(isCorrect);
    // Don't show interim details immediately. 
    // Wait for user to trigger handleNext via onNext prop in QuizView
  };

  const handleManualNext = () => {
    // Show the detail page first, let user study before proceeding
    setShowInterimDetails(true);
  };

  const handleDetailAction = (action) => {
    // Action is now optional or derived from lastQuizResult
    setShowInterimDetails(false);
    let nextStage = tempStage;
    let nextReviewTemp = currentCard.reviewTempStage;
    let isRelearning = false;

    // Determine correctness and next stage
    if (action === 'forgot' || !lastQuizResult) {
      nextStage = 0;
      if (initialReviewMode || nextReviewTemp != null) nextReviewTemp = 0;
      isRelearning = true;
    } else {
      if (tempStage === 'check') {
        if (lastQuizResult) {
          // Check Passed -> Mastered directly
          updateProgress(currentCard.id, { status: 'mastered', reviewTempStage: null });
          handleNext();
          return;
        } else {
          // Check Failed -> Enter Relearning Loop
          nextStage = 0;
          nextReviewTemp = 0;
          isRelearning = true;
        }
      } else {
        // Normal progression
        nextStage = (typeof tempStage === 'number' ? tempStage : 0) + 1;
        if (initialReviewMode || nextReviewTemp != null) nextReviewTemp = nextStage;
      }
    }

    // Update Progress
    if (nextStage >= 3) {
      // Mastered!
      updateProgress(currentCard.id, { status: 'mastered', learningStage: 3, reviewTempStage: null });
      handleNext();
    } else {
      // Not yet mastered -> Re-insert into queue
      const updatedCard = { ...currentCard, learningStage: nextStage, reviewTempStage: nextReviewTemp };
      updateProgress(currentCard.id, { learningStage: nextStage, reviewTempStage: nextReviewTemp });

      // Re-insertion Logic
      // Insert at currentIndex + 4 to +8 (random), or end of array
      const offset = 4 + Math.floor(Math.random() * 5);
      const insertIndex = Math.min(currentIndex + offset, cards.length);

      const newCards = [...cards];
      newCards.splice(insertIndex, 0, updatedCard);
      setCards(newCards);

      // 使用新数组长度判断是否应该继续
      // 因为 setCards 是异步的，handleNext 会使用旧的 cards.length
      // 所以我们直接在这里处理 next 逻辑
      if (currentIndex < newCards.length - 1) {
        setCurrentIndex(prev => prev + 1);
      } else {
        alert("🎉 本组学习完成！休息一下吧！");
        onExit();
      }
    }
  };

  // 优先检查 showInterimDetails，确保详情页能在任何阶段显示
  if (showInterimDetails) {
    return (
      <div className="w-full h-full p-4 md:p-6 max-w-6xl mx-auto flex flex-col md:flex-row gap-6">
        <div className="flex-1 bg-white rounded-3xl shadow-xl border border-slate-100 overflow-hidden flex flex-col">
          <div className="p-6 border-b border-slate-50 flex justify-between items-center bg-slate-50/50">
            <h2 className="text-2xl font-bold text-slate-800">{currentCard.cn} <span className="text-sm font-normal text-slate-400 ml-2">{currentCard.en}</span></h2>
            <div className="text-sm text-slate-400">{currentCard.chapter.split(" ")[0]}</div>
          </div>
          <div className="flex-grow flex flex-col md:flex-row p-6 gap-6 overflow-y-auto">
            <div className="w-full md:w-1/3 aspect-square bg-white rounded-xl border border-slate-100 p-4 flex items-center justify-center">
              <img src={getImagePath ? getImagePath(currentCard.image, imageRotation) : currentCard.image} className="w-full h-full object-contain" />
            </div>
            <div className="flex-1 space-y-4">
              <div>
                <h4 className="font-bold text-indigo-600 mb-2 flex items-center gap-2"><BookOpen /> 考点精要</h4>
                <ul className="space-y-2">
                  {(KEY_POINTS_DB[currentCard.en] || KEY_POINTS_DB[currentCard.cn] || ["暂无详细考点"]).map((p, i) => (
                    <li key={i} className="text-slate-600 text-sm leading-relaxed p-2 bg-slate-50 rounded-lg">{p}</li>
                  ))}
                </ul>
              </div>
              <div className={`p-4 rounded-xl flex items-center gap-3 ${lastQuizResult ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'}`}>
                {lastQuizResult ? <CheckCircle size={24} weight="fill" /> : <WarningCircle size={24} weight="fill" />}
                <div>
                  <p className="font-bold">{lastQuizResult ? "回答正确" : "回答错误"}</p>
                  <p className="text-xs opacity-80">{lastQuizResult ? "点击「下一个」累积熟练度" : "熟练度已重置，请加强记忆"}</p>
                </div>
              </div>
            </div>
          </div>
          <div className="p-4 bg-slate-50 border-t border-slate-100 grid grid-cols-2 gap-4">
            <button
              onClick={() => handleDetailAction('forgot')}
              className="py-3 rounded-xl bg-white border border-rose-200 text-rose-500 font-bold hover:bg-rose-50 transition shadow-sm"
            >
              <ArrowCounterClockwise className="inline mr-2" /> 记错了 / 重来
            </button>
            <button
              onClick={() => handleDetailAction('next')}
              className="py-3 rounded-xl bg-indigo-600 text-white font-bold hover:bg-indigo-700 transition shadow-lg shadow-indigo-200"
            >
              下一个 <CaretRight className="inline ml-2" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (tempStage === 'check') {
    return (
      <div className="flex flex-col items-center justify-center p-6 h-full">
        <div className="bg-white p-8 rounded-3xl shadow-xl max-w-2xl w-full text-center border border-indigo-50 flex flex-col items-center">
          <div className="w-full h-80 mb-6 bg-slate-50 rounded-xl flex items-center justify-center p-4">
            <img src={getImagePath ? getImagePath(currentCard.image, imageRotation) : currentCard.image} alt="Structure" className="max-w-full max-h-full object-contain" />
          </div>
          <h2 className="text-2xl font-bold text-slate-800 mb-6">这个药物熟悉吗？</h2>
          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={() => { setLastQuizResult(false); setTempStage(0); setQuizOptions(generateOptions(currentCard, cards.concat(cardData), 3)); updateProgress(currentCard.id, { reviewTempStage: 0 }); }}
              className="py-3 rounded-xl bg-rose-100 text-rose-600 font-bold hover:bg-rose-200"
            >
              不熟悉
            </button>
            <button
              onClick={() => { setLastQuizResult(true); setShowInterimDetails(true); }}
              className="py-3 rounded-xl bg-emerald-100 text-emerald-600 font-bold hover:bg-emerald-200"
            >
              熟悉
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (tempStage === 0) {
    return (
      <QuizView
        card={currentCard}
        mode="identify-name"
        options={quizOptions}
        onAnswer={onQuizAnswer}
        onNext={handleManualNext}
        progress={0}
        getImagePath={getImagePath}
        imageRotation={imageRotation}
      />
    );
  }

  if (tempStage === 1) {
    return (
      <div className="flex flex-col items-center justify-center p-6 h-full">
        <div className="bg-white p-8 rounded-3xl shadow-xl max-w-2xl w-full text-center border border-indigo-50 flex flex-col items-center">
          <div className="w-full h-80 mb-6 bg-slate-50 rounded-xl flex items-center justify-center p-4">
            <img src={getImagePath ? getImagePath(currentCard.image, imageRotation) : currentCard.image} alt="Structure" className="max-w-full max-h-full object-contain" />
          </div>
          <h2 className="text-2xl font-bold text-slate-800 mb-6">这个药物结构熟悉吗？</h2>
          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={() => { onQuizAnswer(false); handleManualNext(); }}
              className="py-3 rounded-xl bg-slate-100 text-slate-600 font-bold hover:bg-slate-200"
            >
              不熟悉
            </button>
            <button
              onClick={() => { onQuizAnswer(true); handleManualNext(); }}
              className="py-3 rounded-xl bg-indigo-100 text-indigo-600 font-bold hover:bg-indigo-200"
            >
              熟悉
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (tempStage === 2) {
    return (
      <QuizView
        card={currentCard}
        mode="identify-structure"
        options={quizOptions}
        onAnswer={onQuizAnswer}
        onNext={handleManualNext}
        progress={2}
        getImagePath={getImagePath}
        imageRotation={imageRotation}
      />
    );
  }

  // 兜底处理：如果 tempStage 是其他值（如 3 或未定义），默认显示 stage 0
  // 这不应该发生，但作为保险措施
  console.warn('LearningFlow: Unexpected tempStage value:', tempStage, 'Defaulting to stage 0');
  return (
    <QuizView
      card={currentCard}
      mode="identify-name"
      options={quizOptions.length > 0 ? quizOptions : generateOptions(currentCard, cards.concat(cardData), 3)}
      onAnswer={onQuizAnswer}
      onNext={handleManualNext}
      progress={0}
      getImagePath={getImagePath}
      imageRotation={imageRotation}
    />
  );
}

// --- Component: Catalog View (分章节目录) ---

// --- Component: Exam Mode Setup (模拟考试配置) ---
function ExamModeView({ chapters, allCards, disabledDrugs, onStartExam, onExit }) {
  const [selectedChapters, setSelectedChapters] = useState([]);
  const [nameQuestionCount, setNameQuestionCount] = useState(10);
  const [structureQuestionCount, setStructureQuestionCount] = useState(5);
  const [useRealisticMode, setUseRealisticMode] = useState(true);

  // 计算可用药物数量
  const availableStats = useMemo(() => {
    const filtered = allCards.filter(c =>
      (selectedChapters.length === 0 || selectedChapters.includes(c.chapter)) &&
      !disabledDrugs.includes(c.id)
    );
    const allCount = filtered.length;
    const masterCount = filtered.filter(c => c.type === 'master').length;
    return { allCount, masterCount };
  }, [allCards, selectedChapters, disabledDrugs]);

  const toggleChapter = (chapter) => {
    setSelectedChapters(prev =>
      prev.includes(chapter)
        ? prev.filter(c => c !== chapter)
        : [...prev, chapter]
    );
  };

  const selectAll = () => setSelectedChapters([...chapters]);
  const deselectAll = () => setSelectedChapters([]);

  const canStart = selectedChapters.length > 0 &&
    availableStats.allCount >= nameQuestionCount &&
    availableStats.masterCount >= structureQuestionCount;

  const handleStart = () => {
    if (!canStart) return;
    onStartExam({
      selectedChapters,
      nameQuestionCount,
      structureQuestionCount,
      useRealisticMode
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-rose-50 to-purple-100 flex flex-col items-center justify-center p-6">
      <div className="bg-white rounded-3xl shadow-2xl max-w-2xl w-full overflow-hidden border border-slate-100">
        {/* Header */}
        <div className="bg-gradient-to-r from-rose-500 to-purple-600 p-6 text-white">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
              <Exam size={28} weight="fill" />
            </div>
            <div>
              <h2 className="text-2xl font-bold">模拟考试</h2>
              <p className="text-white/80 text-sm">选择章节，开始模拟测试</p>
            </div>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* 章节选择 */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-bold text-slate-800">选择章节</h3>
              <div className="flex gap-2">
                <button onClick={selectAll} className="text-xs px-3 py-1 bg-indigo-50 text-indigo-600 rounded-full hover:bg-indigo-100 transition">全选</button>
                <button onClick={deselectAll} className="text-xs px-3 py-1 bg-slate-50 text-slate-500 rounded-full hover:bg-slate-100 transition">清空</button>
              </div>
            </div>
            <div className="max-h-48 overflow-y-auto border border-slate-200 rounded-xl p-2 space-y-1">
              {chapters.map(ch => (
                <label
                  key={ch}
                  className={`flex items-center gap-3 p-2 rounded-lg cursor-pointer transition ${selectedChapters.includes(ch) ? 'bg-indigo-50 text-indigo-700' : 'hover:bg-slate-50'}`}
                >
                  <input
                    type="checkbox"
                    checked={selectedChapters.includes(ch)}
                    onChange={() => toggleChapter(ch)}
                    className="w-4 h-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="text-sm font-medium">{ch}</span>
                </label>
              ))}
            </div>
          </div>

          {/* 题目设置 */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-slate-50 rounded-xl p-4">
              <label className="block text-sm font-bold text-slate-700 mb-2">
                📝 写药名题
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min="1"
                  max="20"
                  value={nameQuestionCount}
                  onChange={(e) => setNameQuestionCount(Math.max(1, Math.min(20, parseInt(e.target.value) || 1)))}
                  className="w-16 px-3 py-2 border border-slate-200 rounded-lg text-center font-bold"
                />
                <span className="text-sm text-slate-500">道</span>
              </div>
              <p className="text-xs text-slate-400 mt-2">从掌握+熟悉药抽取</p>
              <p className="text-xs text-indigo-500 mt-1">可用: {availableStats.allCount} 个</p>
            </div>

            <div className="bg-slate-50 rounded-xl p-4">
              <label className="block text-sm font-bold text-slate-700 mb-2">
                ✏️ 写结构题
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={structureQuestionCount}
                  onChange={(e) => setStructureQuestionCount(Math.max(1, Math.min(10, parseInt(e.target.value) || 1)))}
                  className="w-16 px-3 py-2 border border-slate-200 rounded-lg text-center font-bold"
                />
                <span className="text-sm text-slate-500">道</span>
              </div>
              <p className="text-xs text-slate-400 mt-2">仅从掌握药抽取</p>
              <p className="text-xs text-indigo-500 mt-1">可用: {availableStats.masterCount} 个</p>
            </div>
          </div>

          {/* 拟真模式 */}
          <label className="flex items-center gap-3 p-4 bg-amber-50 rounded-xl cursor-pointer border border-amber-100">
            <input
              type="checkbox"
              checked={useRealisticMode}
              onChange={(e) => setUseRealisticMode(e.target.checked)}
              className="w-5 h-5 rounded border-amber-300 text-amber-600 focus:ring-amber-500"
            />
            <div>
              <span className="font-bold text-amber-800">启用拟真模式</span>
              <p className="text-xs text-amber-600">黑白图像 + 随机旋转，模拟真实考场</p>
            </div>
          </label>

          {/* 操作按钮 */}
          <div className="flex gap-3">
            <button
              onClick={onExit}
              className="flex-1 py-3 rounded-xl border border-slate-200 text-slate-600 font-bold hover:bg-slate-50 transition"
            >
              返回
            </button>
            <button
              onClick={handleStart}
              disabled={!canStart}
              className={`flex-1 py-3 rounded-xl font-bold transition shadow-lg ${canStart
                ? 'bg-gradient-to-r from-rose-500 to-purple-600 text-white hover:opacity-90 shadow-purple-200'
                : 'bg-slate-200 text-slate-400 cursor-not-allowed shadow-none'}`}
            >
              开始考试 ({nameQuestionCount + structureQuestionCount} 题)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// --- Component: Exam Test View (模拟考试执行) ---
function ExamTestView({ allCards, config, getImagePath, getRandomRotation, onExit }) {
  const { selectedChapters, nameQuestionCount, structureQuestionCount, useRealisticMode } = config;

  // 生成题目
  const { nameQuestions, structureQuestions } = useMemo(() => {
    const pool = allCards.filter(c => selectedChapters.includes(c.chapter));

    // 随机打乱
    const shuffle = (arr) => [...arr].sort(() => Math.random() - 0.5);

    // 写药名题：所有药物
    const namePool = shuffle(pool);
    const nameQs = namePool.slice(0, nameQuestionCount).map(card => ({
      ...card,
      rotation: useRealisticMode ? getRandomRotation() : 0
    }));

    // 写结构题：仅掌握药
    const structurePool = shuffle(pool.filter(c => c.type === 'master'));
    const structureQs = structurePool.slice(0, structureQuestionCount);

    return { nameQuestions: nameQs, structureQuestions: structureQs };
  }, [allCards, selectedChapters, nameQuestionCount, structureQuestionCount, useRealisticMode, getRandomRotation]);

  const [currentPart, setCurrentPart] = useState('name'); // 'name', 'structure', 'result'
  const [currentIndex, setCurrentIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState({
    name: Array(nameQuestionCount).fill(''),
    structure: Array(structureQuestionCount).fill(false) // 是否已完成
  });
  const [showAnswer, setShowAnswer] = useState(false);

  const currentQuestions = currentPart === 'name' ? nameQuestions : structureQuestions;
  const currentQuestion = currentQuestions[currentIndex];
  const totalQuestions = nameQuestionCount + structureQuestionCount;
  const overallIndex = currentPart === 'name' ? currentIndex : nameQuestionCount + currentIndex;

  const handleNameAnswer = (value) => {
    setUserAnswers(prev => ({
      ...prev,
      name: prev.name.map((a, i) => i === currentIndex ? value : a)
    }));
  };

  const handleNext = () => {
    setShowAnswer(false);
    if (currentPart === 'name') {
      if (currentIndex < nameQuestions.length - 1) {
        setCurrentIndex(prev => prev + 1);
      } else {
        // 进入写结构题
        setCurrentPart('structure');
        setCurrentIndex(0);
      }
    } else if (currentPart === 'structure') {
      if (currentIndex < structureQuestions.length - 1) {
        setCurrentIndex(prev => prev + 1);
      } else {
        // 进入结果页
        setCurrentPart('result');
      }
    }
  };

  const handlePrev = () => {
    setShowAnswer(false);
    if (currentIndex > 0) {
      setCurrentIndex(prev => prev - 1);
    } else if (currentPart === 'structure') {
      setCurrentPart('name');
      setCurrentIndex(nameQuestions.length - 1);
    }
  };

  const toggleStructureDone = () => {
    setUserAnswers(prev => ({
      ...prev,
      structure: prev.structure.map((a, i) => i === currentIndex ? !a : a)
    }));
  };

  // 结果页
  if (currentPart === 'result') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-teal-100 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-3xl shadow-2xl overflow-hidden">
            <div className="bg-gradient-to-r from-emerald-500 to-teal-600 p-6 text-white text-center">
              <CheckCircle size={48} weight="fill" className="mx-auto mb-2" />
              <h2 className="text-2xl font-bold">考试完成</h2>
              <p className="text-white/80">共 {totalQuestions} 道题，请对照答案自评</p>
            </div>

            <div className="p-6 space-y-8">
              {/* Part 1: 写药名题 */}
              <div>
                <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 bg-rose-100 text-rose-600 rounded-lg flex items-center justify-center text-sm font-bold">1</span>
                  写出下列药物的名称（通用名，中文）
                </h3>
                <div className="space-y-3">
                  {nameQuestions.map((q, idx) => (
                    <div key={q.id} className="flex items-center gap-4 p-3 bg-slate-50 rounded-xl">
                      <span className="text-sm text-slate-400 w-6">{idx + 1}.</span>
                      <div className="w-16 h-16 bg-white rounded-lg flex items-center justify-center border border-slate-200 flex-shrink-0">
                        <img
                          src={useRealisticMode ? getImagePath(q.image, q.rotation) : q.image}
                          alt=""
                          className="max-w-full max-h-full object-contain"
                        />
                      </div>
                      <div className="flex-1">
                        <div className="text-xs text-slate-400 mb-1">你的答案:</div>
                        <div className={`font-medium ${!userAnswers.name[idx] ? 'text-slate-300 italic' : 'text-slate-700'}`}>
                          {userAnswers.name[idx] || '(未作答)'}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-xs text-emerald-500 mb-1">正确答案:</div>
                        <div className="font-bold text-emerald-700">{q.cn}</div>
                        <div className="text-xs text-slate-400">{q.en}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Part 2: 写结构题 */}
              <div>
                <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 bg-purple-100 text-purple-600 rounded-lg flex items-center justify-center text-sm font-bold">2</span>
                  写出下列药物的化学结构式
                </h3>
                <div className="space-y-3">
                  {structureQuestions.map((q, idx) => (
                    <div key={q.id} className="flex items-start gap-4 p-4 bg-slate-50 rounded-xl">
                      <span className="text-sm text-slate-400 w-6 pt-1">{idx + 1}.</span>
                      <div className="flex-1">
                        <div className="font-bold text-slate-800">{q.cn}</div>
                        <div className="text-sm text-slate-400 mb-3">{q.en}</div>
                        <div className="text-xs text-slate-400 mb-2">正确结构:</div>
                        <div className="bg-white rounded-lg p-3 border border-slate-200 inline-block">
                          <img src={q.image} alt="" className="max-h-32 object-contain" />
                        </div>
                      </div>
                      <div className={`px-3 py-1 rounded-full text-xs font-bold ${userAnswers.structure[idx] ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-500'}`}>
                        {userAnswers.structure[idx] ? '已作答' : '跳过'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <button
                onClick={onExit}
                className="w-full py-4 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-bold text-lg hover:opacity-90 transition shadow-lg shadow-emerald-200"
              >
                返回主菜单
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 答题页
  return (
    <div className="min-h-screen bg-gradient-to-br from-rose-50 to-purple-100 flex flex-col">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md shadow-sm p-4 sticky top-0 z-50">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <button onClick={onExit} className="text-slate-500 hover:text-slate-700 transition">
            <CaretLeft size={24} weight="bold" />
          </button>
          <div className="text-center">
            <div className="text-sm text-slate-500">
              {currentPart === 'name' ? '第一部分：写药名' : '第二部分：写结构'}
            </div>
            <div className="font-bold text-slate-800">
              {overallIndex + 1} / {totalQuestions}
            </div>
          </div>
          <div className="w-6"></div>
        </div>
        {/* Progress bar */}
        <div className="max-w-4xl mx-auto mt-3">
          <div className="bg-slate-200 h-2 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-rose-500 to-purple-600 transition-all duration-300"
              style={{ width: `${((overallIndex + 1) / totalQuestions) * 100}%` }}
            />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="bg-white rounded-3xl shadow-2xl max-w-2xl w-full overflow-hidden">
          {currentPart === 'name' ? (
            // 写药名题
            <div className="p-6">
              <div className="text-center mb-6">
                <span className="inline-block px-3 py-1 bg-rose-100 text-rose-700 rounded-full text-sm font-bold">
                  写出药名（通用名，中文）
                </span>
              </div>

              <div className="bg-slate-50 rounded-2xl p-6 mb-6 flex items-center justify-center min-h-[250px]">
                <img
                  src={useRealisticMode ? getImagePath(currentQuestion.image, currentQuestion.rotation) : currentQuestion.image}
                  alt="Drug Structure"
                  className="max-w-full max-h-[220px] object-contain"
                />
              </div>

              <div className="space-y-4">
                <input
                  type="text"
                  value={userAnswers.name[currentIndex]}
                  onChange={(e) => handleNameAnswer(e.target.value)}
                  placeholder="请输入药物中文名..."
                  className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl text-lg font-medium focus:border-indigo-500 focus:outline-none transition"
                />

                {showAnswer && (
                  <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4">
                    <div className="text-sm text-emerald-600 mb-1">正确答案:</div>
                    <div className="font-bold text-emerald-800 text-lg">{currentQuestion.cn}</div>
                    <div className="text-sm text-emerald-600">{currentQuestion.en}</div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            // 写结构题
            <div className="p-6">
              <div className="text-center mb-6">
                <span className="inline-block px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-bold">
                  写出化学结构式
                </span>
              </div>

              <div className="text-center mb-6">
                <h2 className="text-3xl font-bold text-slate-800">{currentQuestion.cn}</h2>
                <p className="text-slate-400 text-lg mt-1">{currentQuestion.en}</p>
              </div>

              <div className="bg-slate-50 rounded-2xl p-6 mb-6 min-h-[200px] flex flex-col items-center justify-center border-2 border-dashed border-slate-200">
                {showAnswer ? (
                  <img src={currentQuestion.image} alt="" className="max-h-[180px] object-contain" />
                ) : (
                  <div className="text-center text-slate-400">
                    <p className="mb-2">请在纸上写出该药物的化学结构式</p>
                    <p className="text-sm">完成后点击"已完成"或点击"查看答案"对照</p>
                  </div>
                )}
              </div>

              <div className="flex gap-3">
                <button
                  onClick={toggleStructureDone}
                  className={`flex-1 py-3 rounded-xl font-bold transition ${userAnswers.structure[currentIndex]
                    ? 'bg-emerald-500 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                >
                  {userAnswers.structure[currentIndex] ? '✓ 已完成' : '标记已完成'}
                </button>
                <button
                  onClick={() => setShowAnswer(!showAnswer)}
                  className="flex-1 py-3 rounded-xl bg-indigo-100 text-indigo-700 font-bold hover:bg-indigo-200 transition"
                >
                  {showAnswer ? '隐藏答案' : '查看答案'}
                </button>
              </div>
            </div>
          )}

          {/* Navigation */}
          <div className="px-6 pb-6 flex gap-3">
            <button
              onClick={handlePrev}
              disabled={currentPart === 'name' && currentIndex === 0}
              className="flex-1 py-3 rounded-xl border border-slate-200 text-slate-600 font-bold hover:bg-slate-50 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <CaretLeft className="inline mr-1" /> 上一题
            </button>
            <button
              onClick={handleNext}
              className="flex-1 py-3 rounded-xl bg-gradient-to-r from-rose-500 to-purple-600 text-white font-bold hover:opacity-90 transition shadow-lg shadow-purple-200"
            >
              {currentPart === 'structure' && currentIndex === structureQuestions.length - 1
                ? '完成考试'
                : '下一题'} <CaretRight className="inline ml-1" />
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

// --- Component: Catalog View (分章节目录) ---

function CatalogView({ allCards, chapters, progress, onExit, disabledDrugs, onToggleDrug }) {
  const [selectedChapter, setSelectedChapter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCard, setSelectedCard] = useState(null);

  // 按章节分组
  const cardsByChapter = useMemo(() => {
    const grouped = {};
    chapters.forEach(ch => { grouped[ch] = []; });
    allCards.forEach(card => {
      if (grouped[card.chapter]) {
        grouped[card.chapter].push(card);
      }
    });
    return grouped;
  }, [allCards, chapters]);

  // 过滤和搜索
  const filteredCards = useMemo(() => {
    let cards = selectedChapter === 'all' ? allCards : (cardsByChapter[selectedChapter] || []);
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim();
      cards = cards.filter(c =>
        c.cn.toLowerCase().includes(query) ||
        c.en.toLowerCase().includes(query)
      );
    }
    return cards;
  }, [allCards, selectedChapter, searchQuery, cardsByChapter]);

  // 高亮搜索文字
  const highlightText = (text, query) => {
    if (!query.trim()) return text;
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    const parts = text.split(regex);
    return parts.map((part, i) =>
      regex.test(part) ? <mark key={i} className="bg-yellow-200 px-0.5 rounded">{part}</mark> : part
    );
  };

  // 获取学习状态
  const getCardStatus = (cardId) => {
    const p = progress[cardId];
    if (disabledDrugs.includes(cardId)) return { label: '已禁用', color: 'bg-slate-200 text-slate-400' };
    if (!p) return { label: '未学习', color: 'bg-slate-100 text-slate-500' };
    if (p.status === 'mastered') return { label: '已掌握', color: 'bg-emerald-100 text-emerald-600' };
    if (p.learningStage > 0) return { label: '学习中', color: 'bg-blue-100 text-blue-600' };
    return { label: '未学习', color: 'bg-slate-100 text-slate-500' };
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 to-orange-100 flex flex-col">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md sticky top-0 z-30 shadow-sm border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
          <button
            onClick={onExit}
            className="p-2 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-lg transition flex-shrink-0"
          >
            <CaretLeft weight="bold" />
          </button>

          <h1 className="text-lg font-bold text-slate-800 flex items-center gap-2">
            <Books weight="fill" className="text-amber-600" /> 药物目录
          </h1>

          {/* 搜索框 */}
          <div className="flex-1 max-w-md relative">
            <MagnifyingGlass size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="搜索药物名称..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-100 hover:bg-slate-50 focus:bg-white rounded-xl border border-transparent focus:border-amber-300 focus:ring-2 focus:ring-amber-100 outline-none transition text-sm"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                <X size={16} />
              </button>
            )}
          </div>
        </div>
      </header>

      <div className="flex flex-1 max-w-7xl mx-auto w-full">
        {/* 左侧章节导航 */}
        <aside className="w-64 bg-white/50 backdrop-blur-sm border-r border-slate-200 p-4 hidden md:block overflow-y-auto">
          <h3 className="text-sm font-bold text-slate-500 mb-3 uppercase tracking-wide">章节目录</h3>
          <nav className="space-y-1">
            <button
              onClick={() => setSelectedChapter('all')}
              className={`w-full text-left px-3 py-2.5 rounded-lg text-sm font-medium transition flex items-center justify-between ${selectedChapter === 'all' ? 'bg-amber-100 text-amber-700' : 'hover:bg-slate-100 text-slate-600'}`}
            >
              <span>📚 全部章节</span>
              <span className="text-xs opacity-60">{allCards.length}</span>
            </button>
            {chapters.map(ch => (
              <button
                key={ch}
                onClick={() => setSelectedChapter(ch)}
                className={`w-full text-left px-3 py-2.5 rounded-lg text-sm font-medium transition flex items-center justify-between ${selectedChapter === ch ? 'bg-amber-100 text-amber-700' : 'hover:bg-slate-100 text-slate-600'}`}
              >
                <span className="truncate">{ch.split(' ')[0]}</span>
                <span className="text-xs opacity-60">{cardsByChapter[ch]?.length || 0}</span>
              </button>
            ))}
          </nav>
        </aside>

        {/* 移动端章节选择器 */}
        <div className="md:hidden p-4 bg-white border-b border-slate-200">
          <select
            value={selectedChapter}
            onChange={(e) => setSelectedChapter(e.target.value)}
            className="w-full px-3 py-2 bg-slate-100 rounded-lg text-sm border-none outline-none"
          >
            <option value="all">📚 全部章节 ({allCards.length})</option>
            {chapters.map(ch => (
              <option key={ch} value={ch}>{ch.split(' ')[0]} ({cardsByChapter[ch]?.length || 0})</option>
            ))}
          </select>
        </div>

        {/* 右侧卡片网格 */}
        <main className="flex-1 p-4 md:p-6 overflow-y-auto">
          {filteredCards.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-slate-400">
              <MagnifyingGlass size={48} className="mb-4 opacity-50" />
              <p>未找到匹配的药物</p>
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="mt-2 text-amber-600 hover:text-amber-700 text-sm font-medium"
                >
                  清除搜索
                </button>
              )}
            </div>
          ) : (
            <>
              <div className="mb-4 text-sm text-slate-500">
                共 <span className="font-bold text-slate-700">{filteredCards.length}</span> 个药物
                {searchQuery && <span> · 搜索结果</span>}
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                {filteredCards.map(card => {
                  const status = getCardStatus(card.id);
                  const isDisabled = disabledDrugs.includes(card.id);
                  return (
                    <div
                      key={card.id}
                      className={`group bg-white rounded-2xl shadow-sm hover:shadow-xl border border-slate-100 overflow-hidden transition-all duration-300 hover:-translate-y-1 text-left relative ${isDisabled ? 'opacity-60 grayscale' : ''}`}
                    >
                      {/* 禁用 Toggle */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onToggleDrug(card.id);
                        }}
                        className={`absolute top-2 right-2 z-20 p-1.5 rounded-full transition-colors ${isDisabled
                          ? 'bg-slate-200 text-slate-500 hover:bg-slate-300'
                          : 'bg-emerald-100 text-emerald-600 hover:bg-emerald-200'
                          }`}
                        title={isDisabled ? "点击启用" : "点击禁用 (不出现在学习中)"}
                      >
                        {isDisabled ? <XCircle size={16} weight="fill" /> : <CheckCircle size={16} weight="fill" />}
                      </button>

                      <div
                        onClick={() => setSelectedCard(card)}
                        className="cursor-pointer"
                      >
                        <div className="aspect-square bg-slate-50 p-3 flex items-center justify-center">
                          <img
                            src={card.image}
                            alt={card.cn}
                            className="w-full h-full object-contain group-hover:scale-105 transition-transform"
                            onError={(e) => { e.currentTarget.style.opacity = 0.3; }}
                          />
                        </div>
                        <div className="p-3">
                          <h4 className="font-bold text-slate-800 text-sm truncate">
                            {highlightText(card.cn, searchQuery)}
                          </h4>
                          <p className="text-xs text-slate-400 truncate mt-0.5">
                            {highlightText(card.en, searchQuery)}
                          </p>
                          <div className="flex items-center justify-between mt-2">
                            <span className={`text-xs px-2 py-0.5 rounded-full ${status.color}`}>
                              {status.label}
                            </span>
                            <span className={`w-2 h-2 rounded-full ${card.type === 'master' ? 'bg-amber-400' : 'bg-sky-400'}`} title={card.type === 'master' ? '默写' : '识图'}></span>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </main>
      </div>

      {/* 详情弹窗 */}
      {selectedCard && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedCard(null)}
        >
          <div
            className="bg-white rounded-3xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* 弹窗头部 */}
            <div className="p-6 border-b border-slate-100 flex items-start justify-between bg-slate-50">
              <div>
                <h2 className="text-2xl font-bold text-slate-800">{selectedCard.cn}</h2>
                <p className="text-slate-400 font-mono text-sm mt-1">{selectedCard.en}</p>
                <div className="flex items-center gap-2 mt-3">
                  <span className="text-xs px-2 py-1 rounded-full bg-slate-200 text-slate-600">{selectedCard.chapter.split(' ')[0]}</span>
                  <span className={`text-xs px-2 py-1 rounded-full ${selectedCard.type === 'master' ? 'bg-amber-100 text-amber-700' : 'bg-sky-100 text-sky-700'}`}>
                    {selectedCard.type === 'master' ? '默写模式' : '识图模式'}
                  </span>
                  <span className={`text-xs px-2 py-1 rounded-full ${getCardStatus(selectedCard.id).color}`}>
                    {getCardStatus(selectedCard.id).label}
                  </span>
                </div>
              </div>
              <button
                onClick={() => setSelectedCard(null)}
                className="p-2 hover:bg-slate-200 rounded-full transition"
              >
                <X size={20} />
              </button>
            </div>

            {/* 弹窗内容 */}
            <div className="flex-1 overflow-y-auto p-6 flex flex-col md:flex-row gap-6">
              {/* 结构图 */}
              <div className="w-full md:w-1/2 aspect-square bg-white rounded-xl border border-slate-100 p-4 flex items-center justify-center flex-shrink-0">
                <img
                  src={selectedCard.image}
                  alt={selectedCard.cn}
                  className="w-full h-full object-contain"
                />
              </div>

              {/* 考点要求 */}
              <div className="flex-1">
                <h4 className="font-bold text-indigo-600 mb-3 flex items-center gap-2">
                  <BookOpen weight="fill" /> 考点精要
                </h4>
                <ul className="space-y-2">
                  {(KEY_POINTS_DB[selectedCard.en] || KEY_POINTS_DB[selectedCard.cn] || [
                    selectedCard.type === 'master' ? "【掌握】结构、理化性质、体内代谢及临床用途" : "【熟悉】结构特点及临床用途",
                    "【提示】请参考教材详细内容"
                  ]).map((point, idx) => (
                    <li key={idx} className="text-slate-600 text-sm leading-relaxed p-3 bg-slate-50 rounded-lg">
                      {point}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// --- Component: Main App ---
function App() {
  // Major State
  const [currentMajor, setCurrentMajor] = useState(() => {
    try {
      const saved = localStorage.getItem('drug_cards_major');
      return saved || 'med';
    } catch (e) { return 'med'; }
  });

  useEffect(() => {
    localStorage.setItem('drug_cards_major', currentMajor);
  }, [currentMajor]);

  // Realistic Mode State (拟真考试模式)
  const [realisticMode, setRealisticMode] = useState(() => {
    try {
      return localStorage.getItem('drug_cards_realistic') === 'true';
    } catch (e) { return false; }
  });

  useEffect(() => {
    localStorage.setItem('drug_cards_realistic', realisticMode.toString());
  }, [realisticMode]);

  // Helper: Get image path based on realistic mode (with random rotation suffix)
  const getImagePath = useCallback((imagePath, rotation = null) => {
    if (realisticMode && imagePath) {
      // 处理药化专业图片目录
      if (imagePath.includes('/assets/images/')) {
        let monoPath = imagePath.replace('/assets/images/', '/assets/images_mono/');

        // 添加旋转后缀 (如果指定了旋转角度)
        if (rotation && rotation !== 0) {
          // /assets/images_mono/Drug.svg -> /assets/images_mono/Drug_r90.svg
          monoPath = monoPath.replace('.svg', `_r${rotation}.svg`);
        }

        return monoPath;
      }

      // 处理非药化专业图片目录
      if (imagePath.includes('/assets/images_non_med/')) {
        let monoPath = imagePath.replace('/assets/images_non_med/', '/assets/images_non_med_mono/');

        // 添加旋转后缀 (如果指定了旋转角度)
        if (rotation && rotation !== 0) {
          monoPath = monoPath.replace('.svg', `_r${rotation}.svg`);
        }

        return monoPath;
      }
    }
    return imagePath;
  }, [realisticMode]);

  // Helper: Get random rotation angle for realistic mode (0, 90, 180, 270)
  const getRandomRotation = useCallback(() => {
    const rotations = [0, 90, 180, 270];
    return rotations[Math.floor(Math.random() * rotations.length)];
  }, []);

  // Data State
  const allCards = useMemo(() => {
    return currentMajor === 'med' ? cardData : nonMedData;
  }, [currentMajor]);

  const chapters = useMemo(() => [...new Set(allCards.map(d => d.chapter))], [allCards]);

  // View State: 'home', 'learning', 'review', 'card', 'exam', 'exam-test', 'catalog'
  const [currentView, setCurrentView] = useState('home');

  // Exam Mode State
  const [examConfig, setExamConfig] = useState(null);

  // Filter State
  const [selectedChapter, setSelectedChapter] = useState("all");
  const [studyMode, setStudyMode] = useState("mix");
  const [reviewWeakness, setReviewWeakness] = useState(false);

  // Card State
  const [filteredCards, setFilteredCards] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [showEditor, setShowEditor] = useState(false);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [showKeyPoints, setShowKeyPoints] = useState(false);

  // Editor/Verification State
  const [userSmiles, setUserSmiles] = useState("");
  const [verificationResult, setVerificationResult] = useState(null);
  const jsmeRef = useRef(null);
  const showTimerRef = useRef(null);

  // Data Management State
  const [showSettingsModal, setShowSettingsModal] = useState(false);

  // Progress Persistence
  const [progress, setProgress] = useState(() => {
    try {
      const saved = localStorage.getItem('drug_cards_progress');
      return saved ? JSON.parse(saved) : {};
    } catch (e) { return {}; }
  });

  useEffect(() => {
    localStorage.setItem('drug_cards_progress', JSON.stringify(progress));
  }, [progress]);


  const resetCardState = useCallback(() => {
    setIsFlipped(false);
    setUserSmiles("");
    setVerificationResult(null);
    setShowKeyPoints(false);
    setShowEditor(false);
    jsmeRef.current = null;
    if (showTimerRef.current) clearTimeout(showTimerRef.current);
    // Only verify editor is needed in 'card' mode
    if (currentView === 'card') {
      showTimerRef.current = setTimeout(() => setShowEditor(true), 100);
    }
  }, [currentView]);

  // Shuffle Logic
  useEffect(() => {
    let cards = allCards;
    if (selectedChapter !== "all") {
      cards = cards.filter(c => c.chapter === selectedChapter);
    }
    if (studyMode !== "mix") {
      cards = cards.filter(c => c.type === studyMode);
    }
    if (reviewWeakness) {
      const weakCards = cards.filter(c => progress[c.id] === 'unknown');
      cards = weakCards.length > 0 ? weakCards : [];
    }

    if (cards.length > 0) {
      const shuffled = [...cards].sort(() => Math.random() - 0.5);
      setFilteredCards(shuffled);
      setCurrentIndex(0);
      resetCardState();
    } else {
      setFilteredCards([]);
    }
  }, [allCards, selectedChapter, studyMode, reviewWeakness, progress, resetCardState]);

  const currentCard = filteredCards[currentIndex];

  const handleNext = useCallback(() => {
    if (!filteredCards.length) return;
    setIsTransitioning(true);
    // ...
    // Note: This handleNext is specifically for "Card Mode" (Classic)
    // We should ensure we don't mix logic.
    setTimeout(() => {
      if (currentIndex < filteredCards.length - 1) {
        setCurrentIndex(prev => prev + 1);
        resetCardState();
      } else {
        alert("🎉 本轮复习完成！卡片将重新洗牌。");
        setFilteredCards(prev => [...prev].sort(() => Math.random() - 0.5));
        setCurrentIndex(0);
        resetCardState();
      }
      setIsTransitioning(false);
    }, 300);
  }, [filteredCards.length, currentIndex, resetCardState]);

  const markResult = useCallback((status) => {
    if (!currentCard) return;
    // Classic mode update: simple unknown/known
    updateProgress(currentCard.id, { status });
    handleNext();
  }, [currentCard, handleNext]);

  // Unified Progress Updater
  const updateProgress = (id, updates) => {
    setProgress(prev => ({
      ...prev,
      [id]: {
        ...(prev[id] || {}), // preserve existing
        ...updates,
        lastReviewed: Date.now()
      }
    }));
  };

  // Stats Calculation
  const stats = useMemo(() => {
    let learningCount = 0;
    let reviewCount = 0;
    allCards.forEach(c => {
      const p = progress[c.id] || {};
      const status = p.status || 'unknown';
      // "Learning" pool: Not mastered
      if (status !== 'mastered') learningCount++;
      // "Review" pool: Mastered
      if (status === 'mastered') reviewCount++;
    });
    return { learningCount, reviewCount };
  }, [allCards, progress]);

  // Disabled Drugs State (Toggle Feature)
  const [disabledDrugs, setDisabledDrugs] = useState(() => {
    try {
      const saved = localStorage.getItem('drug_cards_disabled');
      return saved ? JSON.parse(saved) : [];
    } catch (e) { return []; }
  });

  useEffect(() => {
    localStorage.setItem('drug_cards_disabled', JSON.stringify(disabledDrugs));
  }, [disabledDrugs]);

  const toggleDrug = (id) => {
    setDisabledDrugs(prev => {
      if (prev.includes(id)) {
        return prev.filter(d => d !== id);
      } else {
        return [...prev, id];
      }
    });
  };

};

// --- Import / Export Logic ---
const handleExportData = () => {
  const data = {
    version: "1.0",
    exportedAt: new Date().toISOString(),
    data: {
      disabledDrugs,
      progress: progress,
      // Also export preferences if needed, but maybe optional
      preferences: {
        currentMajor,
        realisticMode
      }
    }
  };

  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `drug_cards_backup_${new Date().toISOString().split('T')[0]}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

const handleImportData = (e) => {
  const file = e.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (event) => {
    try {
      const json = JSON.parse(event.target.result);
      if (!json.data) throw new Error("无效的备份文件格式");

      // Confirm before overwrite
      if (window.confirm("确定要导入该文件吗？\n当前的所有学习进度将被覆盖，此操作不可撤销！")) {
        if (json.data.disabledDrugs && Array.isArray(json.data.disabledDrugs)) {
          setDisabledDrugs(json.data.disabledDrugs);
        }
        if (json.data.progress && typeof json.data.progress === 'object') {
          setProgress(json.data.progress);
        }
        // Optional: Restore preferences
        if (json.data.preferences) {
          if (json.data.preferences.currentMajor) setCurrentMajor(json.data.preferences.currentMajor);
          if (json.data.preferences.realisticMode !== undefined) setRealisticMode(json.data.preferences.realisticMode);
        }

        alert("✅ 数据恢复成功！");
        setShowSettingsModal(false);
      }
    } catch (err) {
      console.error(err);
      alert("❌ 导入失败：文件格式错误或已损坏");
    }
  };
  reader.readAsText(file);
  // Reset input
  e.target.value = null;
};

// View Switching Logic which prepares cards
const enterMode = (mode, orderMode = 'sequential', chapter = 'all') => {
  let cards = [];

  // 获取基础卡片集（按章节筛选）
  let baseCards = allCards;
  if (chapter !== 'all') {
    baseCards = allCards.filter(c => c.chapter === chapter);
  }

  // 全局过滤：移除被禁用的药物
  // 注意：Catalog模式不过滤，因为我们需要在目录里去开关它
  if (mode !== 'catalog') {
    baseCards = baseCards.filter(c => !disabledDrugs.includes(c.id));
  }

  if (mode === 'learning') {
    cards = generateLearningBatch(baseCards, progress, orderMode, 15);
  } else if (mode === 'review') {
    // Filter: Mastered
    cards = baseCards.filter(c => progress[c.id]?.status === 'mastered');
    // Inject review temp stage (if exists)
    cards = cards.map(c => ({
      ...c,
      learningStage: 3,
      reviewTempStage: (progress[c.id]?.reviewTempStage)
    }));

    // Sort: Prioritize those with reviewTempStage (in-progress re-learning)
    cards.sort((a, b) => {
      const aHas = a.reviewTempStage != null;
      const bHas = b.reviewTempStage != null;
      if (aHas && !bHas) return -1;
      if (!aHas && bHas) return 1;
      return Math.random() - 0.5;
    });

    // For normal review items, set tempStage to 'check' (special stage for Deep Review init)
    cards = cards.map(c => c.reviewTempStage == null ? { ...c, reviewTempStage: 'check' } : c);

  } else if (mode === 'card') {
    // Classic Mode (Filtered by existing UI controls)
    // Logic handled in existing useEffect, but we need to trigger it.
    // We'll just set view.
    // (Existing useEffect [allCards, selectedChapter...] will run and setFilteredCards)
  } else if (mode === 'exam') {
    // Exam setup mode - no card prep needed
    setCurrentView('exam');
    return;
  } else if (mode === 'catalog') {
    // Catalog mode doesn't need filtered cards, it manages its own state
    setCurrentView(mode);
    return;
  }

  if ((mode === 'learning' || mode === 'review') && cards.length === 0) {
    alert(mode === 'learning' ? "太棒了！所有卡片都已掌握！(或者所有卡片都被禁用了)" : "暂无需要深度复习的卡片。");
    return;
  }

  if (mode !== 'card') {
    setFilteredCards(cards);
  }
  setCurrentView(mode);
};

// Keyboard Shortcuts
useEffect(() => {
  const handleKeyDown = (e) => {
    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
    if (e.code === "Space") {
      e.preventDefault();
      setIsFlipped(prev => !prev);
    } else if (e.code === "ArrowRight") {
      if (isFlipped) markResult('known');
    } else if (e.code === "ArrowLeft") {
      if (isFlipped) markResult('unknown');
    }
  };
  window.addEventListener("keydown", handleKeyDown);
  return () => window.removeEventListener("keydown", handleKeyDown);
}, [isFlipped, markResult]);

// --- 使用JSME内置的InChI功能进行离线验证 ---
// InChI是标准化的分子标识符，同一分子会生成相同的InChI
const computeInchiFromSmiles = async (smiles, timeout = 5000) => {
  return new Promise((resolve) => {
    // 设置超时
    const timer = setTimeout(() => {
      console.warn('InChI计算超时');
      resolve(null);
    }, timeout);

    if (!window.JSApplet) {
      console.warn('JSApplet未定义');
      clearTimeout(timer);
      resolve(null);
      return;
    }

    if (!window.JSApplet.Inchi) {
      console.warn('JSME InChI模块未加载，尝试加载...');
      // InChI模块可能需要单独加载
      clearTimeout(timer);
      resolve(null);
      return;
    }

    try {
      // JSME的InChI计算是异步的
      window.JSApplet.Inchi.computeInchi(smiles, (inchi) => {
        clearTimeout(timer);
        console.log('InChI计算结果:', inchi);
        resolve(inchi || null);
      });
    } catch (e) {
      console.warn('InChI计算异常:', e);
      clearTimeout(timer);
      resolve(null);
      return; // Fixed: returned early
    }
  });
};

// 对SMILES进行排序规范化（简单的离线规范化）
const sortSmiles = (smiles) => {
  if (!smiles) return '';
  // 移除立体化学标记
  let s = smiles.replace(/@+/g, '').replace(/[\/\\]/g, '');
  // 分割成片段，排序后重组
  const fragments = s.split('.');
  return fragments.map(f => f.toUpperCase()).sort().join('.');
};

// 从SMILES提取精确的分子式（用于比较）
const extractMolecularFormula = (smiles) => {
  if (!smiles) return {};
  const counts = { C: 0, H: 0, N: 0, O: 0, S: 0, F: 0, Cl: 0, Br: 0, I: 0, P: 0 };

  // 移除立体化学标记和电荷
  let s = smiles.replace(/@+/g, '').replace(/[\/\\]/g, '');

  // 计算双键和环的数量（会影响氢原子数）
  let doubleBonds = (s.match(/=/g) || []).length;
  let tripleBonds = (s.match(/#/g) || []).length;
  let rings = 0;
  for (let i = 1; i <= 9; i++) {
    const ringMatches = s.match(new RegExp(i.toString(), 'g')) || [];
    rings += Math.floor(ringMatches.length / 2);
  }

  // 计算各原子数量
  // 处理 Cl 和 Br（两个字符的原子）
  const clMatches = s.match(/Cl/gi) || [];
  counts.Cl = clMatches.length;
  s = s.replace(/Cl/gi, '');

  const brMatches = s.match(/Br/gi) || [];
  counts.Br = brMatches.length;
  s = s.replace(/Br/gi, '');

  // 单字符原子
  counts.C = (s.match(/c/gi) || []).length;
  counts.N = (s.match(/n/gi) || []).length;
  counts.O = (s.match(/o/gi) || []).length;
  counts.S = (s.match(/s/gi) || []).length;
  counts.F = (s.match(/F/gi) || []).length;
  counts.I = (s.match(/I/gi) || []).length;
  counts.P = (s.match(/P/gi) || []).length;

  // 计算氢原子数（根据价态规则）
  // 简化计算：不精确计算H，只比较重原子

  return counts;
};

// 比较两个分子式是否相同
const compareMolecularFormulas = (formula1, formula2) => {
  const atoms = ['C', 'N', 'O', 'S', 'F', 'Cl', 'Br', 'I', 'P'];
  for (const atom of atoms) {
    if ((formula1[atom] || 0) !== (formula2[atom] || 0)) {
      return false;
    }
  }
  return true;
};

// --- Offline Verification Logic ---
const verifyStructureWithSmiles = async (smiles) => {
  if (!currentCard || !smiles) {
    return;
  }
  setUserSmiles(smiles);
  setVerificationResult("loading");

  const target = currentCard.smiles;

  if (!target) {
    setVerificationResult("error");
    console.warn("No target SMILES found for this card");
    return;
  }

  const userS = smiles.trim();
  const targetS = target.trim();

  console.log('=== SMILES验证开始 ===');
  console.log('用户输入:', userS);
  console.log('目标答案:', targetS);

  // 统一的成功处理函数：显示"正确"提示后自动跳转下一张
  const handleSuccess = (methodName) => {
    console.log(`✓ ${methodName}匹配成功`);
    setVerificationResult("correct");

    // 1.2秒后自动标记为"认识"并切换到下一张
    setTimeout(() => {
      markResult('known');
    }, 1200);
  };

  // 1. 精确匹配
  if (userS === targetS) {
    handleSuccess('精确');
    return;
  }

  // 2. 忽略大小写和立体化学后比较
  const userNorm = sortSmiles(userS);
  const targetNorm = sortSmiles(targetS);
  console.log('规范化后 - 用户:', userNorm);
  console.log('规范化后 - 目标:', targetNorm);

  if (userNorm === targetNorm) {
    handleSuccess('规范化');
    return;
  }

  // 3. 比较分子式（处理芳香环格式差异）
  const userFormula = extractMolecularFormula(userS);
  const targetFormula = extractMolecularFormula(targetS);
  console.log('分子式 - 用户:', JSON.stringify(userFormula));
  console.log('分子式 - 目标:', JSON.stringify(targetFormula));

  if (compareMolecularFormulas(userFormula, targetFormula)) {
    handleSuccess('分子式');
    return;
  }

  // 3. 尝试InChI比较
  console.log('尝试InChI比较...');
  try {
    const [userInchi, targetInchi] = await Promise.all([
      computeInchiFromSmiles(userS),
      computeInchiFromSmiles(targetS)
    ]);

    console.log('用户InChI:', userInchi);
    console.log('目标InChI:', targetInchi);

    if (userInchi && targetInchi) {
      // 比较InChI核心部分（忽略立体化学层）
      const extractCore = (inchi) => {
        if (!inchi) return '';
        const parts = inchi.split('/');
        return parts.slice(0, 4).join('/');
      };

      const userCore = extractCore(userInchi);
      const targetCore = extractCore(targetInchi);
      console.log('InChI核心 - 用户:', userCore);
      console.log('InChI核心 - 目标:', targetCore);

      if (userCore === targetCore) {
        handleSuccess('InChI');
        return;
      }
    } else {
      console.warn('InChI计算失败或模块不可用');
    }
  } catch (e) {
    console.error('InChI比较出错:', e);
  }

  // 所有方法都失败，判定为错误
  console.log('✗ 所有比较方法都未能匹配');
  setVerificationResult("incorrect");
};

const handleCheckDrawing = () => {
  const applet = jsmeRef.current;
  if (!applet) return;
  verifyStructureWithSmiles(applet.smiles());
};

// --- Render Views ---

if (currentView === 'home') {
  return (
    <>
      <MainMenu
        onSelectMode={enterMode}
        stats={stats}
        currentMajor={currentMajor}
        onSwitchMajor={setCurrentMajor}
        chapters={chapters}
        realisticMode={realisticMode}
        onToggleRealisticMode={() => setRealisticMode(prev => !prev)}
        onOpenSettings={() => setShowSettingsModal(true)}
      />
      <DataManagementModal
        isOpen={showSettingsModal}
        onClose={() => setShowSettingsModal(false)}
        onExport={handleExportData}
        onImport={handleImportData}
      />
    </>
  );
}

if (currentView === 'exam') {
  return (
    <ExamModeView
      chapters={chapters}
      allCards={allCards}
      disabledDrugs={disabledDrugs}
      onStartExam={(config) => {
        setExamConfig(config);
        setCurrentView('exam-test');
      }}
      onExit={() => setCurrentView('home')}
    />
  );
}

if (currentView === 'exam-test' && examConfig) {
  return (
    <ExamTestView
      allCards={allCards.filter(c => !disabledDrugs.includes(c.id))}
      config={examConfig}
      getImagePath={getImagePath}
      getRandomRotation={getRandomRotation}
      onExit={() => {
        setExamConfig(null);
        setCurrentView('home');
      }}
    />
  );
}

if (currentView === 'catalog') {
  return (
    <CatalogView
      allCards={allCards}
      chapters={chapters}
      progress={progress}
      onExit={() => setCurrentView('home')}
      disabledDrugs={disabledDrugs}
      onToggleDrug={toggleDrug}
    />
  );
}

if (!filteredCards.length) {
  return (
    <div className="min-h-screen bg-indigo-50 flex flex-col items-center justify-center p-6 text-center">
      <div className="bg-white p-8 rounded-2xl shadow-xl max-w-md w-full">
        <Flask size={64} weight="fill" className="text-indigo-300 mb-4 mx-auto" />
        <h2 className="text-2xl font-bold text-slate-800 mb-2">暂无卡片</h2>
        <p className="text-slate-500 mb-6">
          {reviewWeakness
            ? "太棒了！您目前没有标记为“不认识”的错题。"
            : "当前筛选条件下没有找到卡片，请尝试调整章节或模式。"}
        </p>
        <button
          onClick={() => { setReviewWeakness(false); setSelectedChapter("all"); }}
          className="bg-indigo-600 text-white px-6 py-2 rounded-full font-medium hover:bg-indigo-700 transition"
        >
          重置所有筛选
        </button>
      </div>
    </div>
  );
}

if (currentView === 'learning') {
  return (
    <div className="min-h-screen bg-indigo-50">
      <header className="bg-white px-4 py-3 shadow-sm flex items-center justify-between">
        <button onClick={() => setCurrentView('home')} className="p-2 text-slate-500 hover:bg-slate-100 rounded-full"><CaretLeft size={24} /></button>
        <div className="flex items-center gap-2">
          <h1 className="font-bold text-slate-700">顺序学习</h1>
          {realisticMode && <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full font-bold">拟真</span>}
        </div>
        <div className="w-10"></div>
      </header>
      <div className="h-[calc(100vh-64px)] overflow-hidden">
        <LearningFlow
          cards={filteredCards}
          updateProgress={updateProgress}
          onExit={() => setCurrentView('home')}
          getImagePath={getImagePath}
          realisticMode={realisticMode}
        />
      </div>
    </div>
  );
}

if (currentView === 'review') {
  return (
    <div className="min-h-screen bg-purple-50">
      <header className="bg-white px-4 py-3 shadow-sm flex items-center justify-between">
        <button onClick={() => setCurrentView('home')} className="p-2 text-slate-500 hover:bg-slate-100 rounded-full"><CaretLeft size={24} /></button>
        <div className="flex items-center gap-2">
          <h1 className="font-bold text-slate-700">深度复习</h1>
          {realisticMode && <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full font-bold">拟真</span>}
        </div>
        <div className="w-10"></div>
      </header>
      <div className="h-[calc(100vh-64px)] overflow-hidden">
        <LearningFlow
          cards={filteredCards}
          initialReviewMode={true}
          updateProgress={updateProgress}
          onExit={() => setCurrentView('home')}
          getImagePath={getImagePath}
          realisticMode={realisticMode}
        />
      </div>
    </div>
  );
}

// Fallback to Classic 'card' view (existing UI)
if (!currentCard) return <div className="min-h-screen flex items-center justify-center text-indigo-500">加载中...</div>;

const progressPercent = ((currentIndex + 1) / filteredCards.length) * 100;

const keyPoints = currentCard ? (KEY_POINTS_DB[currentCard.en] || KEY_POINTS_DB[currentCard.cn] || [
  currentCard.type === 'master' ? "【掌握】结构、理化性质、体内代谢及临床用途" : "【熟悉】结构特点及临床用途",
  "【提示】请参考教材详细内容"
]) : [];

return (
  <div className="min-h-screen flex flex-col bg-gradient-to-br from-blue-50 to-indigo-100 font-sans">


    {/* Header */}
    <header className="bg-white/80 backdrop-blur-md sticky top-0 z-30 shadow-sm border-b border-slate-100">
      <div className="max-w-5xl mx-auto px-4 py-3">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentView('home')} // Back to Menu
              className="p-2 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-lg transition"
            >
              <CaretLeft weight="bold" />
            </button>
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white">
              <Flask weight="bold" className="text-xl" />
            </div>
            <h1 className="text-lg font-bold text-slate-800 tracking-tight">药化智能卡片 <span className="text-indigo-600 text-xs px-1.5 py-0.5 bg-indigo-100 rounded-full align-top ml-1">Pro Local</span></h1>
          </div>

          <div className="flex items-center gap-2 overflow-x-auto pb-1 md:pb-0 no-scrollbar">
            <select
              value={selectedChapter}
              onChange={(e) => setSelectedChapter(e.target.value)}
              className="bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm rounded-lg px-3 py-1.5 outline-none focus:ring-2 focus:ring-indigo-500/50 transition cursor-pointer appearance-none border-none min-w-[120px]"
            >
              <option value="all">📚 全书章节</option>
              {chapters.map(ch => <option key={ch} value={ch}>{ch.split(" ")[0]}</option>)}
            </select>

            <select
              value={studyMode}
              onChange={(e) => setStudyMode(e.target.value)}
              className="bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm rounded-lg px-3 py-1.5 outline-none focus:ring-2 focus:ring-indigo-500/50 transition cursor-pointer border-none"
            >
              <option value="mix">🔁 混合</option>
              <option value="familiarize">👀 识图</option>
              <option value="master">✏️ 默写</option>
            </select>

            <button
              onClick={() => setReviewWeakness(!reviewWeakness)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition whitespace-nowrap ${reviewWeakness ? 'bg-amber-100 text-amber-700 ring-2 ring-amber-200' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
            >
              <WarningCircle weight="fill" /> 只看错题
            </button>
          </div>
        </div>
        <div className="w-full bg-slate-200 h-1 mt-3 rounded-full overflow-hidden">
          <div className="bg-indigo-500 h-full transition-all duration-500 ease-out" style={{ width: `${progressPercent}%` }}></div>
        </div>
      </div>
    </header>

    {/* Main Content */}
    <main className="flex-grow flex flex-col items-center justify-center p-4 md:p-6 w-full mx-auto max-w-[1600px] transition-all duration-500">
      <div className={`w-full flex flex-col lg:flex-row items-center ${showKeyPoints ? 'lg:items-start' : 'justify-center'} gap-6 transition-all duration-500 ${showKeyPoints ? 'max-w-full' : 'max-w-6xl mx-auto'}`}>

        {/* Card Container */}
        <div className={`relative w-full ${showKeyPoints ? 'lg:flex-1' : 'max-w-4xl'} aspect-[3/4] sm:aspect-[4/3] perspective-1000 ${isTransitioning ? 'opacity-0 scale-95' : 'opacity-100 scale-100'} transition-all duration-500 ease-in-out`}>
          <div className={`relative w-full h-full transition-transform duration-700 transform-style-3d shadow-2xl rounded-3xl ${isFlipped ? "rotate-y-180" : ""}`}>

            {/* --- Front --- */}
            <div className="absolute w-full h-full bg-white rounded-3xl backface-hidden flex flex-col border border-slate-100 overflow-hidden">
              <div className="p-4 flex justify-between items-start border-b border-slate-50 bg-slate-50/50">
                <span className={`px-3 py-1 rounded-full text-xs font-bold tracking-wide uppercase ${currentCard.type === "master" ? "bg-amber-100 text-amber-700" : "bg-sky-100 text-sky-700"}`}>
                  {currentCard.type === "master" ? "默写模式" : "识图模式"}
                </span>
                <div className="flex flex-col items-end">
                  <span className="text-xs text-slate-400 font-medium">{currentCard.chapter.split(" ")[0]}</span>
                  <span className="text-xs text-slate-300">Card {currentIndex + 1} / {filteredCards.length}</span>
                </div>
              </div>

              <div className="flex-grow relative flex flex-col items-center justify-center p-4 w-full h-full">
                {currentCard.type === "familiarize" ? (
                  /* Changed Container and Image style for perfect fit */
                  <div className="w-full h-full flex items-center justify-center p-2 relative">
                    <img
                      src={currentCard.image}
                      alt="Structure"
                      className="w-full h-full object-contain"
                      onError={(e) => { e.currentTarget.style.opacity = 0.3; e.currentTarget.alt = "Image not found"; }}
                    />
                  </div>
                ) : (
                  <div className="w-full h-full flex flex-col items-center justify-center">
                    <div className="text-center mb-4 flex-shrink-0">
                      <h2 className="text-2xl md:text-3xl font-bold text-slate-800">{currentCard.cn}</h2>
                      <p className="text-sm text-slate-400 font-mono mt-1">{currentCard.en}</p>
                    </div>

                    {/* Editor Container - Enhanced Height */}
                    <div className="w-full flex-grow relative border-2 border-slate-100 rounded-xl bg-slate-50 overflow-hidden shadow-inner group min-h-[300px]">
                      {showEditor ? (
                        <JSMEEditor
                          key={currentCard.id}
                          id={`jsme_${currentCard.id}`}
                          onReady={(applet) => { jsmeRef.current = applet; }}
                          onSmilesChange={(s) => setUserSmiles(s)}
                        />
                      ) : (
                        <div className="flex items-center justify-center h-full text-slate-400 gap-2">
                          <Spinner className="animate-spin text-xl" /> 加载画布...
                        </div>
                      )}

                      {/* Verification Overlay */}
                      {verificationResult && (
                        <div className="absolute inset-0 bg-white/90 backdrop-blur-sm flex flex-col items-center justify-center z-20 fade-in">
                          {verificationResult === "loading" && (
                            <div className="text-indigo-600 flex flex-col items-center">
                              <Spinner className="animate-spin text-4xl mb-2" />
                              <p className="font-medium">AI 正在验证...</p>
                            </div>
                          )}
                          {verificationResult === "correct" && (
                            <div className="text-emerald-500 flex flex-col items-center">
                              <CheckCircle weight="fill" className="text-6xl mb-2 scale-110" />
                              <p className="font-bold text-xl">回答正确！</p>
                            </div>
                          )}
                          {verificationResult === "incorrect" && (
                            <div className="text-rose-500 flex flex-col items-center">
                              <XCircle weight="fill" className="text-6xl mb-2" />
                              <p className="font-bold text-xl">结构不匹配</p>
                              <button onClick={() => setVerificationResult(null)} className="mt-4 px-4 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-full text-sm font-medium transition">
                                再试一次
                              </button>
                            </div>
                          )}
                          {verificationResult === "error" && (
                            <div className="text-amber-600 flex flex-col items-center text-center px-6">
                              <Warning weight="fill" className="text-4xl mb-2" />
                              <p>缺少标准数据，无法自动验证</p>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              <div className="p-4 bg-slate-50 border-t border-slate-100 flex justify-center flex-shrink-0">
                {currentCard.type === "master" ? (
                  <div className="flex gap-3">
                    <button
                      onClick={handleCheckDrawing}
                      disabled={verificationResult === "loading" || verificationResult === "correct"}
                      className={`flex items-center gap-2 px-6 py-2.5 rounded-xl font-bold text-white shadow-lg shadow-indigo-200 transform hover:-translate-y-0.5 transition-all
                        ${verificationResult === "correct" ? "bg-emerald-500" : "bg-indigo-600 hover:bg-indigo-700"} 
                        disabled:opacity-70 disabled:cursor-not-allowed`}
                    >
                      <Check weight="bold" /> 提交验证
                    </button>
                    <button
                      onClick={() => setIsFlipped(true)}
                      className="px-4 py-2.5 rounded-xl font-medium text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 transition"
                    >
                      跳过，看答案
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setIsFlipped(true)}
                    className="w-full py-3 rounded-xl bg-white border border-indigo-100 text-indigo-600 font-bold hover:bg-indigo-50 hover:shadow-md transition-all flex items-center justify-center gap-2"
                  >
                    <Eye weight="bold" /> 点击查看答案 (Space)
                  </button>
                )}
              </div>
            </div>

            {/* --- Back --- */}
            <div className="absolute w-full h-full bg-slate-800 text-white rounded-3xl backface-hidden rotate-y-180 flex flex-col overflow-hidden shadow-2xl ring-1 ring-white/10">
              <div className="p-6 text-center border-b border-white/10 bg-slate-900/50 flex-shrink-0">
                <h2 className="text-2xl font-bold text-indigo-300 mb-1">{currentCard.cn}</h2>
                <p className="text-slate-400 font-mono text-sm">{currentCard.en}</p>
              </div>

              <div className="flex-grow flex items-center justify-center p-6 bg-white mx-4 my-4 rounded-xl shadow-inner overflow-hidden">
                <img
                  src={currentCard.image}
                  alt="Structure Answer"
                  className="w-full h-full object-contain"
                />
              </div>

              <div className="px-6 pb-2 text-center text-slate-400 text-sm flex-shrink-0">
                {currentCard.type === "master" && <p className="mb-2">仔细观察与您画的有何不同？</p>}
                <p className="opacity-60 text-xs mt-4">← 左键忘 / 右键记 →</p>

                <button
                  onClick={(e) => { e.stopPropagation(); setShowKeyPoints(!showKeyPoints); }}
                  className={`mt-4 px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 justify-center transition mx-auto ${showKeyPoints ? 'bg-indigo-600 text-white shadow-md' : 'bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-200 hover:text-white'}`}
                >
                  <BookOpen weight="bold" /> {showKeyPoints ? "关闭考点要求" : "查看考点要求"}
                </button>
              </div>

              <button
                onClick={() => setIsFlipped(false)}
                className="absolute top-4 right-4 w-8 h-8 flex items-center justify-center bg-white/10 hover:bg-white/20 rounded-full text-white/70 hover:text-white transition"
              >
                <ArrowCounterClockwise weight="bold" />
              </button>

              <div className="p-4 grid grid-cols-2 gap-4 bg-slate-900/50 flex-shrink-0">
                <button
                  onClick={() => markResult('unknown')}
                  className="flex flex-col items-center justify-center py-3 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 hover:text-rose-300 border border-rose-500/20 transition group"
                >
                  <XCircle weight="fill" className="text-2xl mb-1 group-hover:scale-110 transition-transform" />
                  <span className="text-xs font-bold">不认识 / 错了</span>
                </button>
                <button
                  onClick={() => markResult('known')}
                  className="flex flex-col items-center justify-center py-3 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 hover:text-emerald-300 border border-emerald-500/20 transition group"
                >
                  <CheckCircle weight="fill" className="text-2xl mb-1 group-hover:scale-110 transition-transform" />
                  <span className="text-xs font-bold">记住了 / 正确</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Side Panel for Key Points */}
        {showKeyPoints && (
          <div className="w-full lg:w-96 bg-white/90 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/20 flex flex-col overflow-hidden animate-slide-in-right h-auto self-stretch max-h-[80vh] lg:max-h-auto flex-shrink-0 transition-all duration-500">
            <div className="p-5 border-b border-slate-100 bg-white/50 flex justify-between items-center">
              <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                <BookOpen className="text-indigo-600" weight="fill" /> 考点要求
              </h3>
              <button onClick={() => setShowKeyPoints(false)} className="text-slate-400 hover:text-slate-600 p-1.5 hover:bg-black/5 rounded-full transition">
                <X size={20} weight="bold" />
              </button>
            </div>

            <div className="p-5 overflow-y-auto custom-scrollbar flex-grow space-y-4">
              <div className="bg-slate-50/80 rounded-xl p-3 border border-slate-100 mb-2">
                <h4 className="text-sm font-bold text-slate-700 mb-1">{currentCard.cn}</h4>
                <p className="text-xs text-slate-400 font-mono">{currentCard.en}</p>
              </div>

              {keyPoints.map((point, idx) => (
                <div key={idx} className="flex gap-3 items-start group">
                  <span className="text-indigo-400 font-bold text-lg mt-0 leading-none group-hover:text-indigo-600 transition-colors">•</span>
                  <p className="text-slate-600 text-sm leading-relaxed font-medium border-b border-slate-50 pb-2 w-full group-hover:text-slate-800 transition-colors">
                    {point}
                  </p>
                </div>
              ))}

              <div className="pt-4 mt-2 border-t border-dashed border-slate-200">
                <p className="text-xs text-slate-400 text-center">
                  {currentCard.type === 'master' ? '重点掌握药物，请结合教材深入复习' : '熟悉药物，主要掌握结构特征与用途'}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="mt-8 text-xs text-slate-400 hidden md:flex gap-6">
        <span className="flex items-center gap-1"><kbd className="bg-white px-1.5 py-0.5 rounded border border-slate-200 font-sans shadow-sm">Space</kbd> 翻页</span>
        <span className="flex items-center gap-1"><kbd className="bg-white px-1.5 py-0.5 rounded border border-slate-200 font-sans shadow-sm">←</kbd> 不认识</span>
        <span className="flex items-center gap-1"><kbd className="bg-white px-1.5 py-0.5 rounded border border-slate-200 font-sans shadow-sm">→</kbd> 认识</span>
      </div>
    </main>
  </div>
);
}

export default App;
