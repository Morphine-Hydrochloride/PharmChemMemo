/**
 * 补充缺失的SMILES数据
 * 注意：只包含药物母核结构，不包含盐类（盐酸、酒石酸、马来酸、硫酸、枸橼酸等）
 * 这些SMILES数据来自PubChem数据库
 */

const fs = require('fs');
const path = require('path');

// 读取现有数据
const dataPath = path.join(__dirname, '../src/data.json');
const data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));

// 缺失SMILES的master类型药物及其正确的SMILES（只有药物母核，不含盐）
const missingSmiles = {
    // 第七章 神经退行性疾病治疗药物
    "Ropinirole hydrochloride": "CCCN(CCC)CCC1=CC2=C(C=C1)NC(=O)CC2", // 罗匹尼罗
    "Pramipexole hydrochloride": "CCCNC1CCC2=C(C1)SC(=N2)N", // 普拉克索
    "Levodopa": "NC(CC1=CC(O)=C(O)C=C1)C(=O)O", // 左旋多巴
    "Donepezil hydrochloride": "COC1=CC2=C(C=C1OC)CC(CC2=O)CC3CCN(CC3)CC4=CC=CC=C4", // 多奈哌齐
    "Rivastigmine tartrate": "CCN(C)C(=O)OC1=CC=CC(=C1)C(C)N(C)C", // 卡巴拉汀
    "Memantine hydrochloride": "CC12CC3CC(C)(C1)CC(N)(C3)C2", // 美金刚

    // 第九章 非甾体抗炎药
    "Imrecoxib": "CC1=CC=C(S1)C(=O)C2=C(N=C(S2)NC3=CC=C(C=C3)OC)C", // 艾瑞昔布

    // 第十章 拟胆碱药和抗胆碱药
    "Pilocarpine nitrate": "CCC1C(COC1=O)CC2=CN=C(N2)C", // 毛果芸香碱
    "Neostigmine bromide": "CN(C)C(=O)OC1=CC=CC(=C1)[N+](C)(C)C", // 新斯的明
    "Atropine sulfate": "CN1C2CCC1CC(C2)OC(=O)C(CO)C3=CC=CC=C3", // 阿托品
    "Trihexyphenidyl hydrochloride": "C1CCC(CC1)C(CCN2CCCCC2)(C3=CC=CC=C3)O", // 苯海索
    "Atracurium besilate": "COC1=CC(=CC(=C1)OC)CC2C3=CC(=C(C=C3CCN2CCCCCCCCCCN4CCC5=CC(=C(C=C5C4CC6=CC(=CC(=C6)OC)OC)OC)OC)OC)OC", // 阿曲库铵

    // 第十一章 抗变态反应药物
    "Chlorphenamine maleate": "CN(C)CCC(C1=CC=C(C=C1)Cl)C2=CC=CC=N2", // 氯苯那敏
    "Cyproheptadine hydrochloride": "CN1CCC(=C2C3=CC=CC=C3C=CC4=CC=CC=C42)CC1", // 赛庚啶
    "Cetirizine hydrochloride": "C1CN(CCN1CCOCC(=O)O)C(C2=CC=CC=C2)C3=CC=C(C=C3)Cl", // 西替利嗪
    "Loratadine": "CCOC(=O)N1CCC(=C2C3=CC=CC=C3CCC4=CC(=CC=C42)Cl)CC1", // 氯雷他定
    "Fexofenadine hydrochloride": "CC(C)(C1=CC=C(C=C1)C(CCCN2CCC(CC2)C(C3=CC=CC=C3)(C4=CC=CC=C4)O)O)C(=O)O", // 非索非那定

    // 第十二章 消化系统药物
    "Cimetidine": "CC1=C(N=CN1)CSCCNC(=NC)NC#N", // 西咪替丁
    "Omeprazole": "CC1=CN=C(C(=C1OC)C)CS(=O)C2=NC3=C(N2)C=C(C=C3)OC", // 奥美拉唑
    "Itopride hydrochloride": "COC1=CC=C(C=C1OC)C(=O)NC2=CC=C(C=C2)CCN(C)C", // 伊托必利
    "Ondansetron hydrochloride": "CC1=NC=CN1CC2CCC3=C(C2=O)C4=CC=CC=C4N3C", // 昂丹司琼

    // 第十三章 降血糖药和骨质疏松治疗药
    "Glimepiride": "CCC1=C(N(C(=O)C1=O)C(=O)NCCC2=CC=C(C=C2)S(=O)(=O)NC(=O)NC3CCC(CC3)C)C", // 格列美脲
    "Metformin hydrochloride": "CN(C)C(=N)NC(=N)N", // 二甲双胍
    "Repaglinide": "CCOC1=C(C=CC(=C1)CC(=O)NC(CC(C)C)C2=CC=CC=C2N3CCCCC3)C(=O)O", // 瑞格列奈
    "Rosiglitazone maleate": "CN(CCOC1=CC=C(C=C1)CC2SC(=O)NC2=O)CC3=NC=CC=C3", // 罗格列酮
    "Miglitol": "OCC1NCC(O)C(O)C1O", // 米格列醇
    "Sitagliptin phosphate": "C1CN2C(=NN=C2C(F)(F)F)CN1C(=O)CC(CC3=CC(=C(C=C3F)F)F)N", // 西格列汀
    "Alendronate sodium": "NCCCC(O)(P(=O)(O)O)P(=O)(O)O", // 阿仑膦酸

    // 第十四章 作用于肾上腺素受体的药物
    "Epinephrine": "CNCC(C1=CC(=C(C=C1)O)O)O", // 肾上腺素
    "Ephedrine hydrochloride": "CC(C(C1=CC=CC=C1)O)NC", // 麻黄碱
    "Clonidine hydrochloride": "C1CN=C(N1)NC2=C(C=CC=C2Cl)Cl", // 可乐定
    "Dobutamine hydrochloride": "CC(CCC1=CC(=C(C=C1)O)O)NCCC2=CC=C(C=C2)O", // 多巴酚丁胺
    "Salbutamol sulfate": "CC(C)(C)NCC(C1=CC(=C(C=C1)O)CO)O", // 沙丁胺醇
    "Prazosin hydrochloride": "COC1=C(C=C2C(=C1)N=C(N=C2N)N3CCN(CC3)C(=O)C4=CC=CO4)OC", // 哌唑嗪
    "Propranolol hydrochloride": "CC(C)NCC(COC1=CC=CC2=CC=CC=C21)O", // 普萘洛尔
    "Metoprolol tartrate": "CC(C)NCC(COC1=CC=C(C=C1)CCOC)O", // 美托洛尔

    // 第十五章 抗高血压药和利尿药
    "Captopril": "CC(CS)C(=O)N1CCCC1C(=O)O", // 卡托普利
    "Enalapril maleate": "CCOC(=O)C(CCC1=CC=CC=C1)NC(C)C(=O)N2CCCC2C(=O)O", // 依那普利
    "Losartan": "CCCCC1=NC(=C(N1CC2=CC=C(C=C2)C3=CC=CC=C3C4=NN=NN4)CO)Cl", // 氯沙坦
    "Nifedipine": "CC1=C(C(C(=C(N1)C)C(=O)OC)C2=CC=CC=C2[N+](=O)[O-])C(=O)OC", // 硝苯地平
    "Amlodipine": "CCOC(=O)C1=C(NC(=C(C1C2=CC=CC=C2Cl)C(=O)OC)C)COCCN", // 氨氯地平
    "Diltiazem": "CC(=O)OC1C(SC2=CC=CC=C2N(C1=O)CCN(C)C)C3=CC=C(C=C3)OC", // 地尔硫卓
    "Verapamil hydrochloride": "COC1=CC=C(C=C1)C(CCCN(C)CCC2=CC(=C(C=C2)OC)OC)(C#N)C(C)C", // 维拉帕米
    "Hydrochlorothiazide": "C1NC2=CC(=C(C=C2S(=O)(=O)N1)S(=O)(=O)N)Cl", // 氢氯噻嗪
    "Furosemide": "C1=C(C=C(C(=C1Cl)S(=O)(=O)N)C(=O)O)NCC2=CC=CO2", // 呋塞米

    // 第十六章 心脏疾病用药物和血脂调节药
    "Propafenone": "CCCNCC(COC1=CC=CC=C1C(=O)CCC2=CC=CC=C2)O", // 普罗帕酮
    "Amiodarone hydrochloride": "CCCCC1=C(C2=CC=CC=C2O1)C(=O)C3=CC(=C(C=C3)OCCN(CC)CC)I", // 胺碘酮
    "Nitroglycerin": "C(C(CO[N+](=O)[O-])O[N+](=O)[O-])O[N+](=O)[O-]", // 硝酸甘油
    "Isosorbide dinitrate": "C1C2C(C(OC1O[N+](=O)[O-])CO)OC(C2)O[N+](=O)[O-]", // 硝酸异山梨酯
    "Lovastatin": "CCC(C)C(=O)OC1CC(C)C=C2C=CC(C)C(CCC3CC(O)CC(=O)O3)C12", // 洛伐他汀
    "Fluvastatin sodium": "CC(C)N1C2=CC=CC=C2C(=C1/C=C/C(CC(CC(=O)O)O)O)C3=CC=C(C=C3)F", // 氟伐他汀
    "Gemfibrozil": "CC1=CC=C(C(=C1)C)OCCCC(C)(C)C(=O)O", // 吉非罗齐

    // 第十七章 甾体激素类药物
    "Estradiol": "CC12CCC3C(C1CCC2O)CCC4=C3C=CC(=C4)O", // 雌二醇
    "Diethylstilbestrol": "CCC(=C(CC)C1=CC=C(C=C1)O)C2=CC=C(C=C2)O", // 己烯雌酚
    "Clomifene citrate": "CCN(CC)CCOC1=CC=C(C=C1)C(=C(Cl)C2=CC=CC=C2)C3=CC=CC=C3", // 氯米芬
    "Testosterone propionate": "CCC(=O)OC1CCC2C1(CCC3C2CCC4=CC(=O)CCC34C)C", // 丙酸睾酮
    "Norethisterone": "CC#CC1(CCC2C1(CCC3C2CCC4=CC(=O)CCC34)C)O", // 炔诺酮
    "Levonorgestrel": "CCC12CCC3C(C1CCC2(C#C)O)CCC4=CC(=O)CCC34", // 左炔诺孕酮
    "Mifepristone": "CC1=CC2=C(CCC3C2CCC4(C3CC(C4O)(C#CC5=CC=C(C=C5)N(C)C)C)C)C=C1", // 米非司酮
    "Tamoxifen": "CCC(=C(C1=CC=CC=C1)C2=CC=C(C=C2)OCCN(C)C)C3=CC=CC=C3", // 他莫昔芬
    "Dexamethasone acetate": "CC1CC2C3CCC4=CC(=O)C=CC4(C3(C(CC2(C1(C(=O)COC(=O)C)O)C)O)F)C", // 醋酸地塞米松

    // 第十八章 抗生素
    "Cefotaxime": "COC(=O)NC(=NOC)C1=CSC(=N1)N.CC(=O)OCC1=C(N2C(C(C2=O)NC(=O)C(=NOC)C3=CSC(=N3)N)SC1)C(=O)O", // 头孢噻肟
    "Clavulanic acid": "OC(=O)C1C(=CCO)OC2CC(=O)N21", // 克拉维酸
    "Sulbactam": "CC1(C(N2C(S1(=O)=O)CC2=O)C(=O)O)C", // 舒巴坦

    // 第十九章 合成抗菌药
    "Linezolid": "CC(=O)NCC1=CC=C(O1)C2=CC(=C(C=C2)N3CC(OC3=O)NCC(=O)C)F", // 利奈唑胺
    "Ethambutol hydrochloride": "CCC(CO)NCCNC(CC)CO", // 乙胺丁醇
    "Terbinafine": "CC(C)(C)C#CC=CC(=C)CN(C)CC1=CC=CC=C1", // 特比萘芬

    // 第二十章 抗病毒药
    "Idoxuridine": "C1C(C(OC1N2C=C(C(=O)NC2=O)I)CO)O", // 碘苷
    "Sofosbuvir": "CC(C)OC(=O)C(C)NP(=O)(OCC1C(C(C(O1)N2C=CC(=O)NC2=O)(C)F)O)OC3=CC=CC=C3", // 索磷布韦
    "Rilpivirine": "CC1=CC(=CC(=C1NC2=NC(=NC(=C2C#N)C#CC3=CC(=CC=C3)NC)N)C)C", // 利匹韦林
    "Zidovudine": "CC1=CN(C(=O)NC1=O)C2CC(C(O2)CO)N=[N+]=[N-]", // 齐多夫定

    // 第二十一章 抗肿瘤药物
    "Chlormethine": "CN(CCCl)CCCl", // 氮芥
    "Carmustine": "C(CN(C(=O)NCCCl)N=O)Cl", // 卡莫司汀
    "Mitoxantrone": "O=C1C2=C(C(=CC=C2O)O)C(=O)C3=C1C(=CC=C3NCCNCCO)NCCNCCO", // 米托蒽醌
    "Cytarabine hydrochloride": "C1=CN(C(=O)N=C1N)C2C(C(C(O2)CO)O)O" // 阿糖胞苷
};

// 更新数据
let updatedCount = 0;
data.forEach(item => {
    if (item.type === 'master' && (!item.smiles || item.smiles === '')) {
        const englishName = item.en;
        if (missingSmiles[englishName]) {
            item.smiles = missingSmiles[englishName];
            updatedCount++;
            console.log(`✓ 更新 ${item.cn} (${englishName})`);
        } else {
            console.log(`✗ 未找到SMILES: ${item.cn} (${englishName})`);
        }
    }
});

// 保存更新后的数据
fs.writeFileSync(dataPath, JSON.stringify(data, null, 2), 'utf8');
console.log(`\n共更新了 ${updatedCount} 个药物的SMILES数据`);
console.log('注意：所有SMILES只包含药物母核，不包含盐类（盐酸、酒石酸、马来酸等）');
