(function () {
  const makeReviews = entries => entries.map(([rating, text]) => ({ rating, text }));
  const rule = (label, keywords, priority) => ({ label, keywords, priority });
  const variant = (label, price) => ({ label, price });

  const competitorData = {
    B0C7PJFLPT: {
      brand: "HOTWAVE",
      asin: "B0C7PJFLPT",
      title: "Push Up Board, Portable Pushup Board, Foldable 20 in 1 Push Up Bar | Multifunctional Fitness...",
      price: 69.99,
      originalPrice: null,
      discount: null,
      launchDate: "2023-08-24",
      daysOnSale: 977,
      rankCategory: "#309 in Sports & Outdoors",
      rankSubcategory: "#3 in Strength Training Pushup Stands",
      rating: 4.5,
      reviewCount: 5894,
      material: "丙烯腈-丁二烯-苯乙烯共聚物(ABS)",
      productSize: "--",
      packageSize: "39.12 x 30.23 x 12.19 cm",
      packageWeight: "3.06 kg",
      variants: [],
      sellingPoints: [
        "多功能集成(俯卧撑板+拉力绳+握力器+门锚)",
        "移动便携折叠",
        "适合所有水平",
        "关节友好",
        "颜色分区识别训练部位",
        "可持续性"
      ],
      reviews: makeReviews([
        [5, "一套就能练胸肩背和握力，家里不占地方。"],
        [5, "板子很稳，折叠后收起来也方便，出差带着不重。"],
        [5, "做工整体不错，我第一次用这类板子，上手很快。"],
        [5, "档位很多，学生党也能按自己的力量水平来调。"],
        [4, "午休在办公室练几组也行，收纳起来不占位。"],
        [2, "边缘有毛刺，手摸着不太舒服。"],
        [2, "塑料感很强，质感一般。"],
        [1, "拉力带用几次就担心会断。"],
        [2, "个别配件装上后有点松。"],
        [1, "说明书图示不清楚，第一次装很费劲。"]
      ]),
      analysisRules: {
        positive: [
          rule("一物多用节省空间", ["一套就能", "一物多用", "多功能", "不占地方", "收纳"], 1),
          rule("稳定不滑动", ["很稳", "稳定", "不会晃", "不滑"], 2),
          rule("做工质量好", ["做工", "不错", "结实", "质量"], 3),
          rule("多档位调节适合不同人群", ["档位", "调节", "力量水平", "不同水平"], 4),
          rule("便携收纳", ["折叠", "收起来", "出差", "便携", "带着"], 5)
        ],
        negative: [
          rule("做工毛刺", ["毛刺", "边缘", "粗糙", "割手"], 1),
          rule("塑料感强", ["塑料感", "质感一般", "廉价"], 2),
          rule("拉力带易断", ["拉力带", "断", "担心会断", "拉力"], 3),
          rule("部分配件松动", ["配件", "松", "松垮", "松动"], 4),
          rule("说明书不清晰", ["说明书", "图示", "看不懂", "费劲"], 5)
        ],
        improvement: [
          rule("提升塑料材质质感", ["塑料感", "质感一般", "毛刺"], 1),
          rule("加强拉力带耐用性", ["拉力带", "断", "耐用"], 2),
          rule("优化说明书图文", ["说明书", "图示", "费劲", "看不懂"], 3)
        ],
        audience: [
          rule("青少年", ["青少年", "学生", "孩子", "年轻"], 1),
          rule("家中空间有限者", ["不占地方", "收纳", "空间有限", "小空间"], 2),
          rule("健身新手", ["新手", "入门", "第一次", "初学", "上手"], 3),
          rule("出差旅行人群", ["出差", "旅行", "带着", "便携"], 4)
        ],
        scenarios: [
          rule("家庭健身", ["家里", "家庭", "客厅", "卧室"], 1),
          rule("出差旅行", ["出差", "旅行", "酒店", "路上"], 2),
          rule("办公室碎片时间", ["办公室", "碎片", "午休", "下班"], 3)
        ],
        optimization: {
          corePainPoints: ["解决耐用性", "提升材质质感"],
          upgradeSuggestions: [
            "升级ABS材质为加厚PC",
            "拉力带升级为乳胶材质",
            "增加防滑垫",
            "优化说明书"
          ]
        }
      }
    },
    B0C5DLQNDW: {
      brand: "LALAHIGH",
      asin: "B0C5DLQNDW",
      title: "Push Up Board, 20 in 1 Home Gym Equipment with Ab Roller Wheel & Resistance Bands...",
      price: 59.99,
      originalPrice: 99.99,
      discount: 25,
      launchDate: "2024-01-15",
      daysOnSale: 953,
      rankCategory: "#11,449 in Sports & Outdoors",
      rankSubcategory: "#13 in Strength Training Pushup Stands",
      rating: 4.5,
      reviewCount: 3680,
      material: "聚丙烯(PP)",
      productSize: "31.5cm(宽) x 8英寸",
      packageSize: "40.64 x 28.42 x 15.49 cm",
      packageWeight: "3.00 kg",
      variants: [
        variant("ProMax高级版", 69.99),
        variant("高级套装", 99.99),
        variant("高级版", 39.99),
        variant("高级版", 29.99)
      ],
      sellingPoints: [
        "一体化多功能健身板",
        "可拆卸结构收纳方便",
        "加高标准结构稳定",
        "承重稳固",
        "整合健腹轮+拉力抗阻训练"
      ],
      reviews: makeReviews([
        [5, "家里练很合适，健腹轮和拉力带功能很全。"],
        [5, "搬家或者旅行带着都不重，放在租房小空间里也不占地。"],
        [5, "自己装很快，新手也能上手。"],
        [5, "价格和配件数量都挺值，送礼也拿得出手。"],
        [4, "板子撑着很稳，家庭健身爱好者会喜欢。"],
        [2, "PP材质感觉偏脆，担心用久会裂。"],
        [2, "健腹轮转起来有点卡。"],
        [3, "有些动作对新手来说不太好上手。"],
        [1, "说明书太简略了，看不明白。"]
      ]),
      analysisRules: {
        positive: [
          rule("便携性", ["便携", "带着", "不重", "搬家", "旅行"], 1),
          rule("多功能性", ["功能很全", "健腹轮", "拉力带", "多功能"], 2),
          rule("物有所值", ["挺值", "价格", "配件数量", "划算"], 3),
          rule("安装简单", ["自己装", "安装", "很快", "零件不复杂"], 4),
          rule("承重稳定", ["很稳", "撑着", "放心", "稳定"], 5)
        ],
        negative: [
          rule("塑料材质易裂", ["PP", "偏脆", "会裂", "塑料"], 1),
          rule("健腹轮卡顿", ["健腹轮", "卡", "顺滑", "转起来"], 2),
          rule("部分用户无法使用", ["新手", "不好上手", "无法使用", "动作"], 3),
          rule("说明书不够详细", ["说明书", "简略", "看不明白", "不详细"], 4)
        ],
        improvement: [
          rule("升级材质耐用性", ["偏脆", "会裂", "材质"], 1),
          rule("优化健腹轮顺滑度", ["健腹轮", "卡", "顺滑"], 2),
          rule("完善说明书", ["说明书", "简略", "看不明白"], 3)
        ],
        audience: [
          rule("家庭健身爱好者", ["家庭", "家里", "健身"], 1),
          rule("租房空间小", ["租房", "小户型", "空间小"], 2),
          rule("健身新手", ["新手", "上手", "初学"], 3),
          rule("送礼人群", ["送礼", "礼物"], 4)
        ],
        scenarios: [
          rule("家庭健身", ["家庭", "家里", "客厅"], 1),
          rule("小户型公寓", ["小户型", "公寓", "租房"], 2),
          rule("旅行携带", ["旅行", "携带", "带走"], 3)
        ],
        optimization: {
          corePainPoints: ["解决材质耐用性", "健腹轮顺滑度"],
          upgradeSuggestions: [
            "加厚PP材质",
            "健腹轮升级轴承",
            "增加防滑设计"
          ]
        }
      }
    },
    B09HBLZT15: {
      brand: "MHCYAB",
      asin: "B09HBLZT15",
      title: "Push Up Board for Men - 15-in-1 Foldable Pushup Board with Push Up Bar, Handles & Bands...",
      price: 14.99,
      originalPrice: 114,
      discount: 5,
      launchDate: "2025-09-13",
      daysOnSale: 357,
      rankCategory: "#19,630 in Sports & Outdoors",
      rankSubcategory: "#20 in Strength Training Pushup Stands",
      rating: 4.6,
      reviewCount: 8900,
      material: "聚乙烯(PE), 主体材料, 弹力带500磅",
      productSize: "--",
      packageSize: "32.77 x 19.81 x 9.65 cm",
      packageWeight: "901.62g",
      variants: [
        variant("单板", 14.29),
        variant("", 18.98),
        variant("", 16.98)
      ],
      sellingPoints: [
        "15合1多功能",
        "可折叠便携",
        "男女通用",
        "弹力带可替换",
        "价格亲民"
      ],
      reviews: makeReviews([
        [5, "性价比很高，预算有限也能入手。"],
        [5, "折叠后很便携，出差旅行带着也方便。"],
        [4, "安装步骤不复杂，新手也能自己装。"],
        [5, "价格亲民，青少年和学生也能接受。"],
        [4, "居家客厅练几组很合适，午休在办公室也能用。"],
        [2, "阻力带拉力不太够。"],
        [2, "板子偏薄，摸起来没那么扎实。"],
        [1, "部分配件容易断，耐用性一般。"],
        [2, "说明书不清晰，步骤看着有点乱。"]
      ]),
      analysisRules: {
        positive: [
          rule("性价比高", ["性价比", "预算", "便宜", "划算"], 1),
          rule("便携折叠", ["折叠", "便携", "带着", "方便"], 2),
          rule("安装简单", ["安装", "步骤", "新手", "自己装"], 3),
          rule("适合新手", ["新手", "入手", "上手", "初学"], 4)
        ],
        negative: [
          rule("阻力带拉力不够", ["阻力带", "拉力不够", "不太够", "拉力"], 1),
          rule("塑料偏薄", ["偏薄", "板子", "不扎实", "薄"], 2),
          rule("部分配件易断", ["配件", "容易断", "断", "耐用"], 3),
          rule("说明书不清晰", ["说明书", "不清晰", "步骤", "乱"], 4)
        ],
        improvement: [
          rule("提升阻力带质量", ["阻力带", "拉力不够", "不太够"], 1),
          rule("加厚板材", ["偏薄", "板子", "薄"], 2),
          rule("优化配件耐用性", ["配件", "容易断", "耐用"], 3)
        ],
        audience: [
          rule("健身新手", ["新手", "初学", "上手"], 1),
          rule("上班族", ["上班族", "午休", "办公室", "下班"], 2),
          rule("预算有限者", ["预算", "便宜", "性价比", "划算"], 3),
          rule("青少年", ["青少年", "学生", "年轻"], 4)
        ],
        scenarios: [
          rule("居家客厅", ["居家", "客厅", "家里"], 1),
          rule("出差旅行", ["出差", "旅行", "带着"], 2),
          rule("办公室", ["办公室", "午休", "工位"], 3)
        ],
        optimization: {
          corePainPoints: ["解决耐用性", "提升阻力带质量"],
          upgradeSuggestions: [
            "升级阻力带为高弹乳胶",
            "加厚PE板材",
            "增加防滑设计"
          ]
        }
      }
    }
  };

  const competitorList = Object.values(competitorData);
  const fieldLabels = [
    "售价",
    "原价 / 折扣",
    "上架时间",
    "排名（大类 + 小类）",
    "评分",
    "评论数",
    "材料",
    "产品尺寸",
    "包装尺寸",
    "包装重量"
  ];

  const placeholders = {
    brand: "待填写品牌名",
    asin: "待填写 ASIN",
    price: "--",
    originalPriceDiscount: "-- / --",
    launchDate: "--",
    rank: "--",
    rating: "--",
    reviewCount: "--",
    material: "--",
    productSize: "--",
    packageSize: "--",
    packageWeight: "--"
  };

  const dom = {};
  const templates = {};
  const specs = {};

  function normalizeAsin(value) {
    return String(value || "").trim().toUpperCase();
  }

  function formatMoney(value) {
    if (value === null || value === undefined || value === "") {
      return "--";
    }
    const number = Number(value);
    if (Number.isNaN(number)) {
      return String(value);
    }
    return `$${number.toLocaleString("en-US", { maximumFractionDigits: 2 })}`;
  }

  function formatDiscount(value) {
    if (value === null || value === undefined || value === "") {
      return "--";
    }
    return `-${Number(value)}%`;
  }

  function formatNumber(value) {
    if (value === null || value === undefined || value === "") {
      return "--";
    }
    const number = Number(value);
    if (Number.isNaN(number)) {
      return String(value);
    }
    return new Intl.NumberFormat("zh-CN").format(number);
  }

  function formatLaunchDate(product) {
    if (!product?.launchDate) {
      return "--";
    }
    if (product.daysOnSale === null || product.daysOnSale === undefined) {
      return product.launchDate;
    }
    return `${product.launchDate}（${formatNumber(product.daysOnSale)}天）`;
  }

  function formatRank(product) {
    const parts = [product?.rankCategory, product?.rankSubcategory].filter(Boolean);
    return parts.length ? parts.join(" / ") : "--";
  }

  function formatOriginalPriceDiscount(product) {
    const original = formatMoney(product?.originalPrice);
    const discount = formatDiscount(product?.discount);
    return `${original} / ${discount}`;
  }

  function setStatus(text) {
    dom.statusNodes.forEach(node => {
      node.textContent = text;
    });
  }

  function setText(node, value) {
    if (node) {
      node.textContent = value;
    }
  }

  function setEditable(node, label) {
    if (!node) {
      return;
    }
    node.contentEditable = "true";
    node.spellcheck = false;
    node.setAttribute("role", "textbox");
    node.setAttribute("aria-label", label);
    node.dataset.editable = "true";
  }

  function showToast(message) {
    let toast = document.getElementById("toast-message");
    if (!toast) {
      toast = document.createElement("div");
      toast.id = "toast-message";
      toast.className = "toast-message";
      toast.setAttribute("aria-live", "polite");
      document.body.appendChild(toast);
    }

    toast.textContent = message;
    toast.classList.add("is-visible");

    window.clearTimeout(showToast.timer);
    showToast.timer = window.setTimeout(() => {
      toast?.classList.remove("is-visible");
    }, 1600);
  }

  function captureTemplates() {
    templates.sellingTags = dom.sellingTags?.innerHTML || "";
    templates.sellingNotes = dom.sellingNotes?.innerHTML || "";
    templates.positiveList = dom.positiveList?.innerHTML || "";
    templates.negativeList = dom.negativeList?.innerHTML || "";
    templates.improvementList = dom.improvementList?.innerHTML || "";
    templates.audienceTags = dom.audienceTags?.innerHTML || "";
    templates.scenarioTags = dom.scenarioTags?.innerHTML || "";
    templates.corePainList = dom.corePainList?.innerHTML || "";
    templates.upgradeList = dom.upgradeList?.innerHTML || "";
    templates.variantRow = dom.variantRow?.innerHTML || "";
  }

  function makeItemEditable(element, prefix, index) {
    setEditable(element, `${prefix}${index + 1}`);
  }

  function renderEditableItems(container, values, className, emptyText, prefix, itemTag = "span") {
    if (!container) {
      return;
    }
    container.replaceChildren();

    const list = values && values.length ? values : (emptyText ? [emptyText] : []);
    list.forEach((value, index) => {
      const node = document.createElement(itemTag);
      node.className = className;
      node.textContent = value;
      makeItemEditable(node, prefix, index);
      container.appendChild(node);
    });
  }

  function renderEditableList(container, values, emptyText, prefix) {
    if (!container) {
      return;
    }
    container.replaceChildren();

    const list = values && values.length ? values : (emptyText ? [emptyText] : []);
    list.forEach((value, index) => {
      const li = document.createElement("li");
      li.textContent = value;
      makeItemEditable(li, prefix, index);
      container.appendChild(li);
    });
  }

  function decorateInitialDynamicSections() {
    Object.entries(specs).forEach(([key, spec]) => {
      const container = spec.get();
      if (!container) {
        return;
      }

      Array.from(container.querySelectorAll(spec.selector)).forEach((node, index) => {
        makeItemEditable(node, spec.prefix, index);
      });
    });
  }

  function restoreDynamicTemplates() {
    if (dom.sellingTags) dom.sellingTags.innerHTML = templates.sellingTags;
    if (dom.sellingNotes) dom.sellingNotes.innerHTML = templates.sellingNotes;
    if (dom.positiveList) dom.positiveList.innerHTML = templates.positiveList;
    if (dom.negativeList) dom.negativeList.innerHTML = templates.negativeList;
    if (dom.improvementList) dom.improvementList.innerHTML = templates.improvementList;
    if (dom.audienceTags) dom.audienceTags.innerHTML = templates.audienceTags;
    if (dom.scenarioTags) dom.scenarioTags.innerHTML = templates.scenarioTags;
    if (dom.corePainList) dom.corePainList.innerHTML = templates.corePainList;
    if (dom.upgradeList) dom.upgradeList.innerHTML = templates.upgradeList;
    if (dom.variantRow) dom.variantRow.innerHTML = templates.variantRow;

    decorateInitialDynamicSections();
  }

  function registerDynamicSpecs() {
    specs.sellingTags = {
      get: () => dom.sellingTags,
      selector: ".tag",
      prefix: "卖点"
    };
    specs.sellingNotes = {
      get: () => dom.sellingNotes,
      selector: "li",
      prefix: "卖点验证"
    };
    specs.positiveList = {
      get: () => dom.positiveList,
      selector: "li",
      prefix: "好评点"
    };
    specs.negativeList = {
      get: () => dom.negativeList,
      selector: "li",
      prefix: "差评点"
    };
    specs.improvementList = {
      get: () => dom.improvementList,
      selector: "li",
      prefix: "待改善点"
    };
    specs.audienceTags = {
      get: () => dom.audienceTags,
      selector: ".tag",
      prefix: "使用人群"
    };
    specs.scenarioTags = {
      get: () => dom.scenarioTags,
      selector: ".tag",
      prefix: "使用场景"
    };
    specs.corePainList = {
      get: () => dom.corePainList,
      selector: "li",
      prefix: "核心痛点"
    };
    specs.upgradeList = {
      get: () => dom.upgradeList,
      selector: "li",
      prefix: "升级建议"
    };
    specs.variantRow = {
      get: () => dom.variantRow,
      selector: ".variant-chip",
      prefix: "变体"
    };
  }

  function getKeywordScore(text, keywords) {
    const source = String(text || "").toLowerCase();

    return keywords.reduce((score, keyword) => {
      const needle = String(keyword || "").toLowerCase();
      if (!needle) {
        return score;
      }

      let count = 0;
      let cursor = 0;
      while (true) {
        const index = source.indexOf(needle, cursor);
        if (index === -1) break;
        count += 1;
        cursor = index + needle.length;
      }
      return score + count;
    }, 0);
  }

  function scoreRule(reviews, item) {
    return reviews.reduce((total, review) => {
      return total + getKeywordScore(review.text, item.keywords);
    }, 0);
  }

  function extractLabels(reviews, rules, limit) {
    const scored = rules.map(item => ({
      ...item,
      score: scoreRule(reviews, item)
    }));

    const labels = scored
      .filter(item => item.score > 0)
      .sort((a, b) => a.priority - b.priority)
      .map(item => item.label);

    const orderedRules = rules.slice().sort((a, b) => a.priority - b.priority);
    orderedRules.forEach(item => {
      if (labels.length < limit && !labels.includes(item.label)) {
        labels.push(item.label);
      }
    });

    return labels.slice(0, limit);
  }

  function analyzeProduct(product) {
    const reviews = product.reviews || [];
    const positiveReviews = reviews.filter(review => review.rating >= 4);
    const negativeReviews = reviews.filter(review => review.rating <= 3);

    return {
      positiveReviews,
      negativeReviews,
      positivePoints: extractLabels(positiveReviews, product.analysisRules.positive, 5),
      negativePoints: extractLabels(negativeReviews, product.analysisRules.negative, 5),
      improvementPoints: extractLabels(negativeReviews, product.analysisRules.improvement, 3),
      targetAudience: extractLabels(reviews, product.analysisRules.audience, 4),
      useScenarios: extractLabels(reviews, product.analysisRules.scenarios, 3),
      corePainPoints: product.analysisRules.optimization.corePainPoints,
      upgradeSuggestions: product.analysisRules.optimization.upgradeSuggestions
    };
  }

  function renderBasicInfo(product) {
    setText(dom.brandValue, product.brand);
    setText(dom.asinValue, product.asin);

    const values = [
      formatMoney(product.price),
      formatOriginalPriceDiscount(product),
      formatLaunchDate(product),
      formatRank(product),
      product.rating === null || product.rating === undefined ? "--" : Number(product.rating).toFixed(1),
      formatNumber(product.reviewCount),
      product.material || "--",
      product.productSize || "--",
      product.packageSize || "--",
      product.packageWeight || "--"
    ];

    dom.infoValueNodes.forEach((node, index) => {
      setText(node, values[index] || "--");
    });
  }

  function renderEmptyBasicInfo() {
    setText(dom.brandValue, placeholders.brand);
    setText(dom.asinValue, placeholders.asin);

    const defaults = [
      placeholders.price,
      placeholders.originalPriceDiscount,
      placeholders.launchDate,
      placeholders.rank,
      placeholders.rating,
      placeholders.reviewCount,
      placeholders.material,
      placeholders.productSize,
      placeholders.packageSize,
      placeholders.packageWeight
    ];

    dom.infoValueNodes.forEach((node, index) => {
      setText(node, defaults[index] || "--");
    });
  }

  function renderVariants(product) {
    const values = (product.variants || []).map((item, index) => {
      const label = String(item.label || "").trim() || `变体 ${index + 1}`;
      const price = item.price === null || item.price === undefined ? "" : ` / ${formatMoney(item.price)}`;
      return `${label}${price}`;
    });

    renderEditableItems(dom.variantRow, values, "variant-chip", "暂无公开变体", "变体");
  }

  function renderSellingPoints(product, analysis) {
    renderEditableItems(dom.sellingTags, product.sellingPoints || [], "tag", "暂无卖点数据", "卖点");
    renderEditableList(dom.sellingNotes, analysis.positivePoints, "暂无评论验证卖点", "卖点验证");
  }

  function renderReviewAnalysis(analysis) {
    renderEditableList(dom.positiveList, analysis.positivePoints, "暂无好评点", "好评点");
    renderEditableList(dom.negativeList, analysis.negativePoints, "暂无差评点", "差评点");
    renderEditableList(dom.improvementList, analysis.improvementPoints, "暂无待改善点", "待改善点");
  }

  function renderUserDimensions(analysis) {
    renderEditableItems(dom.audienceTags, analysis.targetAudience, "tag", "暂无使用人群", "使用人群");
    renderEditableItems(dom.scenarioTags, analysis.useScenarios, "tag", "暂无使用场景", "使用场景");
  }

  function renderOptimization(analysis) {
    renderEditableList(dom.corePainList, analysis.corePainPoints, "暂无核心痛点", "核心痛点");
    renderEditableList(dom.upgradeList, analysis.upgradeSuggestions, "暂无升级建议", "升级建议");
  }

  function renderEmptyDynamicSections() {
    restoreDynamicTemplates();
  }

  function readBasicInfoLines() {
    const values = dom.infoValueNodes.map(node => node.textContent.trim() || "--");

    return [
      `品牌：${dom.brandValue?.textContent.trim() || "--"}`,
      `ASIN：${dom.asinValue?.textContent.trim() || "--"}`,
      `售价：${values[0] || "--"}`,
      `原价 / 折扣：${values[1] || "-- / --"}`,
      `上架时间：${values[2] || "--"}`,
      `排名：${values[3] || "--"}`,
      `评分：${values[4] || "--"}`,
      `评论数：${values[5] || "--"}`,
      `材料：${values[6] || "--"}`,
      `产品尺寸：${values[7] || "--"}`,
      `包装尺寸：${values[8] || "--"}`,
      `包装重量：${values[9] || "--"}`
    ];
  }

  function collectTexts(container, selector) {
    if (!container) {
      return [];
    }

    return Array.from(container.querySelectorAll(selector))
      .map(node => node.textContent.trim())
      .filter(Boolean);
  }

  function buildReportText() {
    const basic = readBasicInfoLines();
    const variants = collectTexts(dom.variantRow, ".variant-chip");
    const sellingPoints = collectTexts(dom.sellingTags, ".tag");
    const sellingNotes = collectTexts(dom.sellingNotes, "li");
    const positivePoints = collectTexts(dom.positiveList, "li");
    const negativePoints = collectTexts(dom.negativeList, "li");
    const improvementPoints = collectTexts(dom.improvementList, "li");
    const targetAudience = collectTexts(dom.audienceTags, ".tag");
    const useScenarios = collectTexts(dom.scenarioTags, ".tag");
    const corePainPoints = collectTexts(dom.corePainList, "li");
    const upgradeSuggestions = collectTexts(dom.upgradeList, "li");

    return [
      "亚马逊竞品自动化分析系统",
      "",
      "【基础信息】",
      ...basic,
      "",
      "【变体信息】",
      ...(variants.length ? variants : ["暂无公开变体"]),
      "",
      "【产品卖点】",
      ...(sellingPoints.length ? sellingPoints : ["暂无卖点数据"]),
      "",
      "【卖点验证】",
      ...(sellingNotes.length ? sellingNotes : ["暂无评论验证卖点"]),
      "",
      "【好评点】",
      ...(positivePoints.length ? positivePoints : ["暂无好评点"]),
      "",
      "【差评点】",
      ...(negativePoints.length ? negativePoints : ["暂无差评点"]),
      "",
      "【待改善点】",
      ...(improvementPoints.length ? improvementPoints : ["暂无待改善点"]),
      "",
      "【使用人群】",
      ...(targetAudience.length ? targetAudience : ["暂无使用人群"]),
      "",
      "【使用场景】",
      ...(useScenarios.length ? useScenarios : ["暂无使用场景"]),
      "",
      "【优化方向】",
      "核心解决痛点：",
      ...(corePainPoints.length ? corePainPoints : ["暂无核心痛点"]),
      "升级建议：",
      ...(upgradeSuggestions.length ? upgradeSuggestions : ["暂无升级建议"])
    ].join("\n");
  }

  function findProductByAsin(asin) {
    return competitorData[normalizeAsin(asin)] || null;
  }

  function handleQuery() {
    const asin = normalizeAsin(dom.asinInput?.value);

    if (!asin) {
      setStatus("请输入 ASIN 后再查询。");
      dom.asinInput?.focus();
      return;
    }

    const product = findProductByAsin(asin);

    if (!product) {
      window.alert("暂无该商品数据");
      setStatus(`未找到 ASIN ${asin} 对应的商品数据。`);
      return;
    }

    const analysis = analyzeProduct(product);
    renderBasicInfo(product);
    renderVariants(product);
    renderSellingPoints(product, analysis);
    renderReviewAnalysis(analysis);
    renderUserDimensions(analysis);
    renderOptimization(analysis);

    setStatus(`已加载 ${product.brand} 的评论分析与优化建议，可继续手动微调。`);
    document.getElementById("basicInfo")?.scrollIntoView({
      behavior: "smooth",
      block: "start"
    });
  }

  async function handleCopy() {
    const text = buildReportText();

    try {
      await navigator.clipboard.writeText(text);
      setStatus("已复制完整竞品分析内容。");
      showToast("复制成功");
    } catch (error) {
      window.prompt("复制以下内容：", text);
      setStatus("浏览器限制了剪贴板访问，已打开复制窗口。");
      showToast("复制失败，请手动复制");
    }
  }

  function handleExport() {
    const text = buildReportText();
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "amazon-competitor-report.txt";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);

    setStatus("已导出当前竞品分析文本。");
  }

  function handleReset() {
    if (dom.asinInput) {
      dom.asinInput.value = "";
      dom.asinInput.focus();
    }

    renderEmptyBasicInfo();
    renderEmptyDynamicSections();
    setStatus("已重置为初始状态。");
    showToast("已重置");
  }

  function bindEvents() {
    dom.queryBtn?.addEventListener("click", handleQuery);
    dom.resetBtn?.addEventListener("click", handleReset);
    dom.copyBtn?.addEventListener("click", handleCopy);
    dom.exportBtn?.addEventListener("click", handleExport);

    dom.asinInput?.addEventListener("keydown", event => {
      if (event.key === "Enter") {
        event.preventDefault();
        handleQuery();
      }
    });

    const editableNodes = [dom.brandValue, dom.asinValue, ...dom.infoValueNodes];
    editableNodes.forEach(node => {
      node?.addEventListener("input", () => {
        setStatus("已手动修改基础信息，可继续查询或导出。");
      });
    });

    const dynamicEditableEvents = [
      [dom.sellingTags, ".tag"],
      [dom.sellingNotes, "li"],
      [dom.positiveList, "li"],
      [dom.negativeList, "li"],
      [dom.improvementList, "li"],
      [dom.audienceTags, ".tag"],
      [dom.scenarioTags, ".tag"],
      [dom.corePainList, "li"],
      [dom.upgradeList, "li"],
      [dom.variantRow, ".variant-chip"]
    ];

    dynamicEditableEvents.forEach(([container, selector]) => {
      container?.addEventListener("input", () => {
        if (container.querySelector(selector)) {
          setStatus("已手动微调分析结果。");
        }
      });
    });
  }

  function cacheDom() {
    dom.asinInput = document.getElementById("asinInput");
    dom.queryBtn = document.getElementById("queryBtn");
    dom.resetBtn = document.getElementById("resetBtn");
    dom.copyBtn = document.getElementById("copyBtn");
    dom.exportBtn = document.getElementById("exportBtn");
    dom.statusNodes = document.querySelectorAll("[data-status], [data-action-status]");
    dom.brandValue = document.querySelector(".identity-value");
    dom.asinValue = document.querySelector(".identity-code");
    dom.infoValueNodes = Array.from(document.querySelectorAll(".info-grid .info-item strong"));
    dom.variantRow = document.querySelector("#basicInfo .variant-row");
    dom.sellingTags = document.querySelector('section[aria-labelledby="selling-title"] .tag-cloud');
    dom.sellingNotes = document.querySelector('section[aria-labelledby="selling-title"] .placeholder-list');

    const reviewPanels = document.querySelectorAll('section[aria-labelledby="review-title"] .analysis-panel');
    dom.positiveList = reviewPanels[0]?.querySelector(".analysis-list") || null;
    dom.negativeList = reviewPanels[1]?.querySelector(".analysis-list") || null;
    dom.improvementList = reviewPanels[2]?.querySelector(".analysis-list") || null;

    const userPanels = document.querySelectorAll('section[aria-labelledby="user-title"] .mini-panel');
    dom.audienceTags = userPanels[0]?.querySelector(".tag-cloud") || null;
    dom.scenarioTags = userPanels[1]?.querySelector(".tag-cloud") || null;

    const optPanels = document.querySelectorAll('section[aria-labelledby="opt-title"] .mini-panel');
    dom.corePainList = optPanels[0]?.querySelector(".placeholder-list") || null;
    dom.upgradeList = optPanels[1]?.querySelector(".placeholder-list") || null;
  }

  function setupEditableFields() {
    setEditable(dom.brandValue, "品牌名");
    setEditable(dom.asinValue, "ASIN");

    dom.infoValueNodes.forEach((node, index) => {
      setEditable(node, fieldLabels[index] || "基础信息");
    });
  }

  function init() {
    cacheDom();
    registerDynamicSpecs();
    captureTemplates();
    setupEditableFields();
    decorateInitialDynamicSections();
    renderEmptyBasicInfo();
    renderEmptyDynamicSections();
    bindEvents();

    if (typeof window !== "undefined") {
      window.competitorData = competitorData;
      window.mockData = competitorList;
    }

    setStatus("请输入 ASIN 后查询竞品基础信息。");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
