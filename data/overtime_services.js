/* Minification failed. Returning unminified contents.
(2729,8): run-time error JS1004: Expected ';'
 */
function TranslatorApi($http) {

  var _caller = new ServiceCaller($http, 'translatorService');

  var _dataFolder = SETTINGS.LangFilesUrl;
  var _translatorService = {
    DefaultLanguage: appModule.webConfig.defaultLanguage,
    LearningMode: SETTINGS.TextLearningModeOn,
    _currentLang: appModule.webConfig.defaultLanguage,
    TranslationFileSufix: appModule.webConfig.translationFileSufix,
    _translations: []
  };

  //Private Methods

  function addTextToTranslate (text) {
    _translatorService._translations[text] = "[NT]";
  };

  function getTranslation(text) {
    var txt = _translatorService._translations[text];
    if (txt || txt == "[NT]") return txt;
    txt = _translatorService._translations[text.toUpperCase()];
    return txt;
  };

  function loadLanguage() {
    _caller.GET(_dataFolder + '/data/lang/' + _translatorService._currentLang + _translatorService.TranslationFileSufix + '.json').then(function (response) {
      _translatorService._translations = response.data;
    });
  };

  function makeTextSafeToTranslate(text) {
    var translatedName;
    text = text.replace(/ /g, "_").replace(".5", "H").replace(/½/g, "H").replace(/-/g, "_").toUpperCase();
    var firstChar = text.charAt(0);
    if (/^([0-9])$/.test(firstChar)) {
      translatedName = text.replace(firstChar, CommonFunctions.SubstituteDigitByLetter(firstChar));
    } else {
      translatedName = text;
    }
    return translatedName;
  };

  function saveTranslations() {
    _caller.POST({ 'lang': _translatorService._currentLang + _translatorService.TranslationFileSufix, 'json': JSON.stringify(_translatorService._translations) }, "SaveTranslations").then();
  };

  _translatorService.ChangeLanguage = function (newLang) {
    if (_translatorService._currentLang == newLang) return;
    _translatorService._currentLang = newLang;
    loadLanguage();
  };

  _translatorService.Translate = function (text) {
    if (!text || !_translatorService._translations) return text;
    var safeText = makeTextSafeToTranslate(text);
    var txt = getTranslation(safeText);
    if (txt && txt != "[NT]") return txt;
    else {
      if (_translatorService.LearningMode && txt == "[NT]") {
        //translatorService._translations[safeText] = "[NT]";
        text = "[" + text + "]";
      }
      else if (_translatorService.LearningMode) {
        addTextToTranslate(safeText);
        text = "[" + text + "*NEW*]";
      }
      return text.replace('_', ' ');
    }
  };

  _translatorService.SaveLearnedTexts = function () {
    saveTranslations();
  };

  loadLanguage();

  return _translatorService;

}

if (typeof appModule != "undefined")
  appModule.factory('$translatorService', ['$http', '$rootScope', TranslatorApi]);
else if (typeof loginModule != "undefined")
  loginModule.factory('$translatorService', ['$http', '$rootScope', TranslatorApi || {}]);;
appModule.factory('$wagerTypesService', ['$http', '$rootScope', '$customerService', function ($http, $rootScope, $customerService) {

  var _caller = new ServiceCaller($http, 'BetType');

  var _wagerTypesService = {};

  _wagerTypesService.Ids = {
    StraightBet: 0,
    Parlay: 1,
    Teaser: 2,
    IfWinOrPush: 3,
    IfWinOnly: 4,
    ActionReverse: 5,
    Contest: 6
  };

  _wagerTypesService.SubWagerTypeCode = {
    Spread: "S",
    MoneyLine: "M",
    Total: "L",
    TeamTotal: "E"
  };

_wagerTypesService.SubWagerTypeSymbol = {
    "S": "Spread",
    "M":"MoneyLine",
    "L":"Total",
     "E":"TeamTotal"
};

  _wagerTypesService.Previous = null;
  _wagerTypesService.Selected = null;

  //Private Methods

  function getWagerTypeById(wtId) {
    if (!_wagerTypesService.List) return null;
    for (var i = 0; i < _wagerTypesService.List.length; i++) {
      if (_wagerTypesService.List[i].id == wtId) {
        return _wagerTypesService.List[i];
      }
    }
    return null;
  }

  function getFirstWagerType() {
    if (!_wagerTypesService.List) return null;
    return _wagerTypesService.List[0];
  }

  function setSelected(getFromSession) {
    if (getFromSession) {
      return _caller.POST({}, 'GetCurrent', null, true).then(function (result) {
        var wtId = result.WebCode;
        var previous = _wagerTypesService.Selected;
        var wt = getWagerTypeById(wtId) || getFirstWagerType();
        _wagerTypesService.Selected = wt;
        _wagerTypesService.Previous = previous != null ? previous : _wagerTypesService.Selected;
        $rootScope.$broadcast('wagerTypeChanged');
      });
    }
    else {
      _wagerTypesService.Previous = _wagerTypesService.Selected;
      $rootScope.$broadcast('wagerTypeChanged');
    }
    return true;
  };

  //Public Methods

    _wagerTypesService.getWagerTypeByCode = function (wtCode) {
        return _wagerTypesService.SubWagerTypeSymbol[wtCode] || ' ';
    };

  _wagerTypesService.IsTeaser = function () {
    return (_wagerTypesService.List && _wagerTypesService.Selected && _wagerTypesService.Selected.id == _wagerTypesService.Ids.Teaser);
  };

  _wagerTypesService.IsMultiple = function () {
    return (_wagerTypesService.List && _wagerTypesService.Selected && _wagerTypesService.Selected.multiple);
  };

  _wagerTypesService.IsActionReverse = function () {
    return (_wagerTypesService.List && _wagerTypesService.Selected && _wagerTypesService.Selected.id == _wagerTypesService.Ids.ActionReverse);
  };

  _wagerTypesService.IsStraightBet = function () {
    return (_wagerTypesService.List && _wagerTypesService.Selected && _wagerTypesService.Selected.id == _wagerTypesService.Ids.StraightBet);
  };

  _wagerTypesService.IsParlay = function () {
    return (_wagerTypesService.List && _wagerTypesService.Selected && _wagerTypesService.Selected.id == _wagerTypesService.Ids.Parlay);
  };

  _wagerTypesService.IsIfBet = function () {
    return (_wagerTypesService.List &&
      _wagerTypesService.Selected &&
      (_wagerTypesService.Selected.id == _wagerTypesService.Ids.IfWinOrPush ||
        _wagerTypesService.Selected.id == _wagerTypesService.Ids.IfWinOnly));
  };

  _wagerTypesService.IsIfBetWinOnly = function () {
    return (_wagerTypesService.List &&
      _wagerTypesService.Selected &&
      (_wagerTypesService.Selected.id == _wagerTypesService.Ids.IfWinOnly));
  };

  _wagerTypesService.IsIfBetWinOrPush = function () {
    return (_wagerTypesService.List &&
      _wagerTypesService.Selected &&
      (_wagerTypesService.Selected.id == _wagerTypesService.Ids.IfWinOrPush));
  };

  _wagerTypesService.Change = function () {
    _caller.POST({ 'wagerTypeId': _wagerTypesService.Selected.id }, 'Change').then(function () {
      setSelected(false);
    });
  };

  _wagerTypesService.IsAccumWager = function () {
    if (!_wagerTypesService.Selected) return false;
    return _wagerTypesService.Selected.id != _wagerTypesService.Ids.StraightBet &&
      _wagerTypesService.Selected.id != _wagerTypesService.Ids.IfWinOrPush &&
      _wagerTypesService.Selected.id != _wagerTypesService.Ids.IfWinOnly;
  };

  _wagerTypesService.RevertChange = function () {
    if (!_wagerTypesService.Selected || _wagerTypesService.Selected.id == _wagerTypesService.Previous.id) return false;
    _wagerTypesService.Selected = _wagerTypesService.Previous;
    return true;
  };

  var _filtered = false;
  _wagerTypesService.FilterWagerTypes = function () {
    if (_filtered || !_wagerTypesService.List || !_wagerTypesService.List.length) return;
    if (!$customerService || !$customerService.Restrictions || !$customerService.Restrictions.length) return;
    _filtered = true;
    var noSb = false, noParlay = false, noTeaser = false, noIfbet = false, noAr = false;

    for (var k = 0; k < $customerService.Restrictions.length; k++) {
      var r = $customerService.Restrictions[k];
      if (r.Code == "NOSB") noSb = true;
      if (r.Code == "NOPARLAY") noParlay = true;
      if (r.Code == "NOTEASER") noTeaser = true;
      if (r.Code == "NOIFBET") noIfbet = true;
      if (r.Code == "NOAR") noAr = true;
    }
    if (!noSb && !noParlay && !noTeaser && !noIfbet && !noAr) return;

    var i = _wagerTypesService.List.length;
    while (i--) {
      var wt = _wagerTypesService.List[i];
      if (wt.code == "SB" && noSb) _wagerTypesService.List.splice(i, 1);
      else if (wt.code == "P" && noParlay) _wagerTypesService.List.splice(i, 1);
      else if (wt.code == "T" && noTeaser) _wagerTypesService.List.splice(i, 1);
      else if (wt.code == "I" && noIfbet && wt.id != 5) _wagerTypesService.List.splice(i, 1);
      else if (wt.id == 5 && noAr) _wagerTypesService.List.splice(i, 1);
    }
    if (noSb) {
      _wagerTypesService.Selected = getFirstWagerType();
      _wagerTypesService.Change();
    }
  };

  _wagerTypesService.GetMenuList = function () {
    var l = [];
    var showMultiple = false;
    for (var i = 0; i < _wagerTypesService.List.length; i++) {
      if (!_wagerTypesService.List[i].multiple) l.push(_wagerTypesService.List[i]);
      else if (!showMultiple) {
        _wagerTypesService.List[i].title = 'Multiple';
        l.push(_wagerTypesService.List[i]);
        showMultiple = true;
      }
    }
    return l;
  };

  _caller.GET(appModule.Root +'/data/wagerTypes.json').then(function (response) {
    _wagerTypesService.List = response.data.wagerTypes;
    _wagerTypesService.FilterWagerTypes();
    setSelected(true).then();
  });

  return _wagerTypesService;

}]);;
appModule.factory('$ticketService', ['$http', '$wagerTypesService', '$translatorService', '$systemService', '$customerService', '$rootScope', '$errorHandler', function ($http, $wagerTypesService, $translatorService, $systemService, $customerService, $rootScope, $errorHandler) {

  var _caller = new ServiceCaller($http, 'Betting');

  var _ticketService = {
    ServerClienTimeDiff: null,
    Ticket: {
      TotalRiskAmount: 0,
      TotalToWinAmount: 0,
      ArAmount : 0,
      UseFreePlay: false,
      PlayCount: 0,
      TicketNumber: null,
      WagerItems: [],
      OpenWagerItems: [],
      TeaserName: null,
      TeaserInfo: null,
      ParlayInfo: null,
      RoundRobin: {
        Selected: null,
        Options: []
      },
      AllowedWagerPicks: {
        MinPicks: 1,
        MaxPicks: 999,
        OpenPicks: 999
      },
      wGBS: 0,
      Password: "",
      RiskMax: 0,
      ToWinMax: 0,
            KeepOpenPlay: false,
            ARBCLabel: "ARBC",
            ARBC: false
    },
    SubWagerTypes: {
      Spread: 'S',
      MoneyLine: 'M',
      TotalPoints: 'L',
      TeamTotals: 'E'
    },
    openPlays: [],
    ShowOpenPlayItems: false,
    SelectedOpenSpots: {
      name: "",
      value: 0
    },
    OpenWager: null,
    TicketProcessed: true,
    IsMoverReady: false,
    OpenDisable: false,
    PlacingBet: false,
    offeringSelectedItems: [],
    ActiveRifWager: null,
    ParlayLimits: null
  };

    var _teamsString = ' ' + $translatorService.Translate('open spots');


  _ticketService.openPlaysSelection = [
    {
      name: $translatorService.Translate('No Open Spot'),
      value: _ticketService.Ticket.AllowedWagerPicks.MaxPicks
    }, {
        name: 1 + (_teamsString.replace('open spots', 'open spot')),
      value: 1
    }, {
      name: 2 + _teamsString,
      value: 2
    }, {
      name: 3 + _teamsString,
      value: 3
    }, {
      name: 4 + _teamsString,
      value: 4
    }, {
      name: 5 + _teamsString,
      value: 5
    }, {
      name: 6 + _teamsString,
      value: 6
    }, {
      name: 7 + _teamsString,
      value: 7
    }, {
      name: 8 + _teamsString,
      value: 8
    }, {
      name: 9 + _teamsString,
      value: 9
    }, {
      name: 10 + _teamsString,
      value: 10
    }, {
      name: 11 + _teamsString,
      value: 11
    }, {
      name: 12 + _teamsString,
      value: 12
    }, {
      name: 13 + _teamsString,
      value: 13
    }, {
      name: 14 + _teamsString,
      value: 14
    }, {
      name: 15 + _teamsString,
      value: 15
    }
  ];
  _ticketService.OpenSpotsDropDown = [];
  _ticketService.ContinuePressed = false;

  function validateFreePlayMaxPrice(gameItem, subWagerType, teamPos) {
    if (!_ticketService.Ticket.UseFreePlay) return true;
    var price;
    switch (subWagerType) {
      case "M":
        price = (teamPos == 1) ? gameItem.MoneyLine1 : ((teamPos == 2) ? gameItem.MoneyLine2 : MoneyLine3);
        break;
      case "S":
        price = (teamPos == 1) ? gameItem.SpreadAdj1 : gameItem.SpreadAdj2;
        break;
      case "L":
        price = (teamPos == 1) ? gameItem.TtlPtsAdj1 : gameItem.TtlPtsAdj2;
        break;
      case "E":
        if (teamPos == 1) price = gameItem.Team1TtlPtsAdj1;
        else if (teamPos == 2) price = gameItem.Team2TtlPtsAdj1;
        else if (teamPos == 3) price = gameItem.Team1TtlPtsAdj2;
        else price = gameItem.Team2TtlPtsAdj2;
        break;
    }
    if (price > ($customerService.Info.FreePlayMaxPrice / 100)) {
      UI.Notify($translatorService.Translate("Max free play price allowed is ") + ($customerService.Info.FreePlayMaxPrice / 100), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning, '', 2000);
      return false;
    }
    return true;
  }

  function GameLineAction(gameItem, subWagerType, teamPos, wageringDisabled, sportsWageringDisabled, isDemo) {
    _ticketService.ContinuePressed = false;
    _ticketService.IsMoverReady = false;
    if (!_ticketService.TicketProcessed || isDemo) return;

    if (!_ticketService.Ticket.Any())
      _ticketService.Ticket.UseFreePlay = false;

    if (!validateFreePlayMaxPrice(gameItem, subWagerType, teamPos)) return;

    if (wageringDisabled || sportsWageringDisabled) {
      UI.Alert($translatorService.Translate("Account under read only!"));
      return false;
    }
    var wagerType = $wagerTypesService.Selected;

    switch (subWagerType) {
      case "M":
        gameItem.MoneyLineChanged = false;
        break;
      case "S":
        gameItem.SpreadChanged = false;
        break;
      case "L":
        gameItem.TotalPointsChanged = false;
        break;
      case "E":
        gameItem.TeamTotalChanged = false;
        break;
    }
    var added = revertGameLineSelection(gameItem, subWagerType, teamPos);
    if (added) {
      _ticketService.offeringSelectedItems.push({ gameItem: gameItem, subWagerType: subWagerType, teamPos: teamPos, wageringDisabled: wageringDisabled, sportsWageringDisabled: sportsWageringDisabled, isDemo: isDemo });
            _ticketService.AddGameWagerItem(gameItem, subWagerType, teamPos, wagerType, false).then(function () {
                _ticketService.ValidateParlaySelections(true);
            });
    }
    else {
      _ticketService.RemoveGameWagerItem(gameItem, subWagerType, teamPos, false, null);
      const index = _ticketService.offeringSelectedItems.findIndex(e => gameItem.GameNum == e.gameItem.GameNum && gameItem.ShowDate === e.gameItem.ShowDate && gameItem.PeriodNumber == e.gameItem.PeriodNumber
        && gameItem.IsTitle == e.gameItem.IsTitle && e.subWagerType == subWagerType && e.teamPos == teamPos);
      _ticketService.offeringSelectedItems.splice(index, 1);
            _ticketService.ValidateParlaySelections(true);
    }
      return Promise.resolve(123);

  }

  _ticketService.ValidateParlaySelections = function (changeOpenSpots) {
    if (!$wagerTypesService.IsParlay()) return true;
    if (!_ticketService.Ticket.ParlayInfo || !_ticketService.Ticket.ParlayInfo.ParlayLimits || !_ticketService.Ticket.ParlayInfo.ParlayLimits.length)
      return true;

    var maxPicks = _ticketService.Ticket.ParlayInfo.ParlayMaxPicks;

    var limits = _ticketService.Ticket.ParlayInfo.ParlayLimits;

    var totalSelections = _ticketService.GetTotalWagersAndOpenSpots();
    var origTotalSelections = totalSelections;
    if (totalSelections < 2 || totalSelections > 100) totalSelections = 2;
    var limit = limits.find(l => l.Teams == totalSelections);
    if (!limit) {
      _ticketService.ParlayLimits = null;
      return true;
    }
    var dogsCount = 0;
    var totalsCount = 0;
    var moneyLineCount = 0;
    var result = true;
      if (limit.MaxDogs || limit.TotalsLimit || limit.MoneylinesLimit) {
      var i = 0;
      for (i = 0; i < _ticketService.Ticket.WagerItems.length; i++) {
        var wi = _ticketService.Ticket.WagerItems[i];
        if (wi.WagerType == "M" && ((wi.ChosenTeamIndex == 1 && wi.Loo.MoneyLine1 >= 100 && wi.Loo.MoneyLine1 > wi.Loo.MoneyLine2) || (wi.ChosenTeamIndex == 2 && wi.Loo.MoneyLine2 >= 100 && wi.Loo.MoneyLine2 > wi.Loo.MoneyLine1) || (wi.ControlCode.indexOf("3") >= 0 && wi.Loo.MoneyLineDraw > 100))) dogsCount++;
        else if (wi.WagerType == "S" && ((wi.ChosenTeamIndex == 1 && wi.Loo.SpreadAdj1 >= 100 && wi.Loo.SpreadAdj1 > wi.Loo.SpreadAdj2) || (wi.ChosenTeamIndex == 2 && wi.Loo.SpreadAdj2 >= 100 && wi.Loo.SpreadAdj2 > wi.Loo.SpreadAdj1))) dogsCount++;
        else if (wi.WagerType == "L" && ((wi.TotalPointsOu == 'O' && wi.Loo.TtlPtsAdj1 >= 100 && wi.Loo.TtlPtsAdj1 > wi.Loo.TtlPtsAdj2) || (wi.TotalPointsOu == 'U' && wi.Loo.TtlPtsAdj2 >= 100 && wi.Loo.TtlPtsAdj2 > wi.Loo.TtlPtsAdj1))) dogsCount++;

        if (wi.WagerType == "L") totalsCount++;
          if (wi.WagerType == "M") moneyLineCount++;
      }
      for (i = 0; i < _ticketService.Ticket.OpenWagerItems.length; i++) {
        var wi = _ticketService.Ticket.OpenWagerItems[i];
        if (wi.WagerType == "M" && wi.FinalPrice > 100) dogsCount++;
        if (wi.WagerType == "L") totalsCount++;
          if (wi.WagerType == "M") moneyLineCount++;
      }
      if ((limit.MaxDogs && dogsCount > limit.MaxDogs) || (limit.TotalsLimit && totalsCount > limit.TotalsLimit) || (limit.MoneylinesLimit && moneyLineCount > limit.MoneylinesLimit)) {
        result = false;
      }
    }
    limit.DogsCount = dogsCount;
    limit.TotalsCount = totalsCount;
      limit.MoneylinesCount = moneyLineCount;
    //var limit = limits.find(l => l.Teams == totalSelections);
    if (changeOpenSpots) ChangeParlayOpenSpotOptions(limit, maxPicks, origTotalSelections);
    _ticketService.ParlayLimits = limit;
    return result;
  }

  function ChangeParlayOpenSpotOptions(parlayLimit, maxPicks, totalSelections) {
      if (!_ticketService.OpenSpotsDropDown || !_ticketService.OpenSpotsDropDown.length || _ticketService.IsClosingOpenPlay()) return;
      var availableOpenSpots = maxPicks - totalSelections + 1;
    _ticketService.OpenSpotsDropDown = _ticketService.openPlaysSelection.slice(0, availableOpenSpots);
    _ticketService.SelectedOpenSpots = _ticketService.OpenSpotsDropDown[0];
  }

  function revertGameLineSelection(gameItem, subWagerType, teamPos) {
    var added = false;
    switch (subWagerType) {
      case "S":
        if (teamPos == 1) added = gameItem.Spread1Selected = !gameItem.Spread1Selected;
        else added = gameItem.Spread2Selected = !gameItem.Spread2Selected;
        break;
      case "M":
        if (teamPos == 1) added = gameItem.MoneyLine1Selected = !gameItem.MoneyLine1Selected;
        else if (teamPos == 2) added = gameItem.MoneyLine2Selected = !gameItem.MoneyLine2Selected;
        else added = gameItem.MoneyLine3Selected = !gameItem.MoneyLine3Selected;
        break;
      case "L":
        if (teamPos == 1) added = gameItem.TotalPoints1Selected = !gameItem.TotalPoints1Selected;
        else added = gameItem.TotalPoints2Selected = !gameItem.TotalPoints2Selected;
        break;
      case "E":
        if (teamPos == 1) added = gameItem.Team1TtlPtsAdj1Selected = !gameItem.Team1TtlPtsAdj1Selected;
        else if (teamPos == 2) added = gameItem.Team2TtlPtsAdj1Selected = !gameItem.Team2TtlPtsAdj1Selected;
        else if (teamPos == 3) added = gameItem.Team1TtlPtsAdj2Selected = !gameItem.Team1TtlPtsAdj2Selected;
        else added = gameItem.Team2TtlPtsAdj2Selected = !gameItem.Team2TtlPtsAdj2Selected;
        break;
    }
    added = (added && !_ticketService.Ticket.Posted() && _ticketService.IsClosingOpenPlay() ? _ticketService.IsOpenFull() : added);
    setTimeout(function () {
      if (!added) {
        var el = $('#' + subWagerType + teamPos + '_' + gameItem.GameNum + '_' + gameItem.PeriodNumber);
        el.removeClass('active');
      }
    }, 200);
    return added;
  };

  function prepareWagerData() {
    var wagerItemsData = [];
    var i;
    for (i = 0; i < _ticketService.Ticket.WagerItems.length; i++) {
      var wagerItem = _ticketService.Ticket.WagerItems[i];
      if (wagerItem.Available == false) continue;
      if ($wagerTypesService.IsAccumWager()) {
        var indexWagerItems = _ticketService.TotalWagers() - 1;
        if ($wagerTypesService.IsParlay()) window.WagerAmountOnChange(wagerItem, 'R');
        else if ($wagerTypesService.IsTeaser()) window.WagerAmountOnChange(wagerItem, 'R');
        wagerItem.RiskAmt = _ticketService.Ticket.TotalRiskAmount;
        wagerItem.ToWinAmt = _ticketService.Ticket.TotalToWinAmount;
        if ($wagerTypesService.IsActionReverse()) wagerItem.AmountEntered = "RiskAmt";
      }

      var finalLine = wagerItem.FinalLine;
      var finalPrice = wagerItem.FinalPrice;

      if (wagerItem.SelectedLine != null && wagerItem.WagerType != "M" && wagerItem.WagerType != "E") { // In case of buy points
        finalLine = parseFloat(wagerItem.SelectedLine.points);
        finalPrice = wagerItem.SelectedLine.lineAdj;
        wagerItem.FinalLine = wagerItem.SelectedLine.points;
          wagerItem.FinalPrice = finalPrice;
      }
      if (!wagerItem.ToWinAmt) wagerItem.ToWinAmt = 0;
      var obj;
      if (wagerItem.Type == 'G') {
        var roundRobin = _ticketService.GetSelectedRoundRobin();
        var rrAmt = 0;
        if (roundRobin != null && roundRobin.value != 0) {
          var rrValues = ParlayFunctions.CalculateRoundRobinToWin(_ticketService.Ticket.WagerItems, _ticketService.Ticket.ParlayInfo, _ticketService.Ticket.TotalRiskAmount, roundRobin.value, $customerService.Info.RoundRobinMaxPayout);
          rrAmt = wagerItem.RiskAmt * rrValues.PlayCount;
        }
        obj = {
          'RiskAmount': wagerItem.RiskAmt,
          'ToWinAmount': wagerItem.ToWinAmt,
          'RrAmount': rrAmt,
          'WagerAmt': wagerItem.RiskAmt,
          'ControlCode': wagerItem.ControlCode,
          'FinalLine': finalLine,
          'FinalPrice': finalPrice,
          'GameNum': wagerItem.Loo.GameNum,
          'PeriodNumber': wagerItem.Loo.PeriodNumber,
          'AmountEntered': wagerItem.AmountEntered,
          'pitcher1ReqFlag': wagerItem.WagerType == "M" ? wagerItem.Pitcher1ReqFlag : true,
          'pitcher2ReqFlag': wagerItem.WagerType == "M" ? wagerItem.Pitcher2ReqFlag : true,
          'RoundRobinValue': (roundRobin != null) ? roundRobin.value : 0,
          'PlayCount': _ticketService.Ticket.PlayCount,
          'ArAmount': _ticketService.Ticket.ArAmount,
          'RifTicketNumber': wagerItem.RifTicketNumber,
          'RifWagerNumber': wagerItem.RifWagerNumber,
          'RifWinOnlyFlag': !!wagerItem.RifWinOnlyFlag
        };
      } else
        obj = {
          'RiskAmount': wagerItem.RiskAmt,
          'ToWinAmount': wagerItem.ToWinAmt,
          'WagerAmt': wagerItem.RiskAmt,
          'ContestNum': wagerItem.Loo.ContestNum,
          'ContestantNum': wagerItem.Loo.ContestantNum,
          'FinalPrice': wagerItem.Loo.MoneyLine,
          'FinalLine': wagerItem.Loo.ThresholdLine,
          'ToBase': wagerItem.Loo.ToBase
        };
      wagerItemsData.push(obj);
    };
    return wagerItemsData;
  };

  function newWagerItem(wager) {
    wager.Loo = [];
    return wager;
  };

  function emptyTicket() {
    _ticketService.Ticket.TotalRiskAmount = 0;
    _ticketService.Ticket.TotalToWinAmount = 0;
    _ticketService.Ticket.RRTotalRiskAmount = 0;
    _ticketService.Ticket.ArAmount = 0;
    _ticketService.Ticket.TicketNumber = null;
    _ticketService.Ticket.WagerItems = [];
    _ticketService.Ticket.OpenWagerItems = [];
    _ticketService.Ticket.RoundRobin = {};
    _ticketService.Ticket.wGBS = Math.random() * (70 - 1) + 1;
    _ticketService.Ticket.UseFreePlay = false;
    _ticketService.Ticket.KeepOpenPlay = false;
    _ticketService.PlacingBet = false;
    _ticketService.ChangeSelectedOpenSpots(_ticketService.OpenSpotsDropDown[0]);
    _ticketService.ActiveRifWager = null;
        _ticketService.Ticket.ARBCLabel = $translatorService.Translate("ARBC");
    _ticketService.Ticket.ParentRifWager = {
      TicketNumber: null,
      WagerNumber: null,
      AmountWagered: null
    };
  };

  function getLeagueBuyPointsInfo(sportType, sportSubType, controlCode, wagerType, chosenTeamId, periodNumber) {
    return _caller.POST({ 'sportType': sportType, 'sportSubType': sportSubType, 'controlCode': controlCode, 'wagerType': wagerType, 'chosenTeamId': chosenTeamId, 'periodNumber': periodNumber }, 'GetLeagueBuyPointsInfo', null, true).then();
  };

  function createBuyPointsOptions(wi) {
    if (wi.Loo.PeriodNumber > 0 ||
      wi.Loo.PreventPointBuyingFlag == 'Y' ||
      (wi.Loo.SportType != "Football" && wi.Loo.SportType != "Basketball" && wi.Loo.SportType != "Baseball") ||
      wi.WagerType == 'M' ||
      wi.WagerType == 'E' ||
      $wagerTypesService.IsTeaser()) return false;

    var bpInfo = null;
    getLeagueBuyPointsInfo(wi.Loo.SportType, wi.Loo.SportSubType, wi.ControlCode, $wagerTypesService.Selected.name, wi.ChosenTeamId, wi.Loo.PeriodNumber).then(function (result) {
      bpInfo = result;
      if (bpInfo != null && bpInfo.length > 0) {
        var cont = 0;
        var buyPoints = [];
        bpInfo.forEach(function (bi) {
          var adjustment = "";
          var points = bi.Points == 0 ? 'pk' : LineOffering.ConvertToHalfSymbol(bi.Points, SETTINGS.MaxDenominator);
          switch (wi.PriceType) {
            case "A":
              adjustment = bi.Price > 0 ? '+' + bi.Price : bi.Price;
              break;
            case "D":
              var decimalPrice = CommonFunctions.ConvertPriceToDecimal(bi.Price, CommonFunctions.DecimalPrecision); //pending decimalPrecision
              adjustment += decimalPrice;
              if (decimalPrice == Math.floor(decimalPrice)) {
                adjustment += ".0";
              }
              break;
            case "F":
              decimalPrice = CommonFunctions.ConvertPriceToDecimal(bi.Price, 0);
                adjustment += bi.Numerator;
              adjustment += "/";
                adjustment += bi.Denominator;
              break;
          }
          buyPoints.push({
            'lineAdj': bi.Price,
            'points': bi.Points,
            'strPoints': bi.Points > 0 ? '+' + points : points,
            'cost': adjustment
          });
          if (bi.Points == wi.FinalLine) wi.SelectedLine = buyPoints[buyPoints.length - 1];
        });
        if (!wi.SelectedLine) wi.BuyPoints = null;
        else wi.BuyPoints = buyPoints;
      }
      else wi.SelectedLine = null;
      $rootScope.$broadcast('buyPointsInfoComplete');
    });
    return true;
  };

  function getBlockSTFlags() {
    return {
      QuarterInetParlayFlag: $systemService.Parameters.BlockStQuarterInetParlayFlag,
      BaseballFlag: $systemService.Parameters.BlockStBaseballFlag,
        HockeyFlag: $systemService.Parameters.BlockStHockeyFlag,
        SoccerFlag: $systemService.Parameters.BlockStSoccerFlag
    };
  };

  function revertGameWagerSelection(wagerItem, subWagerType, teamPos) {
    switch (subWagerType) {
      case _ticketService.SubWagerTypes.Spread:
        if (teamPos == 1) wagerItem.Spread1Selected = false;
        else wagerItem.Spread2Selected = false;
        break;
      case _ticketService.SubWagerTypes.MoneyLine:
        if (teamPos == 1) wagerItem.MoneyLine1Selected = false;
        else if (teamPos == 2) wagerItem.MoneyLine2Selected = false;
        else wagerItem.MoneyLine3Selected = false;
        break;
      case _ticketService.SubWagerTypes.TotalPoints:
        if (teamPos == 1) wagerItem.TotalPoints1Selected = false;
        else wagerItem.TotalPoints2Selected = false;
        break;
      case _ticketService.SubWagerTypes.TeamTotals:
        if (teamPos == 1) wagerItem.Team1TtlPtsAdj1Selected = false;
        else if (teamPos == 2) wagerItem.Team2TtlPtsAdj1Selected = false;
        else if (teamPos == 3) wagerItem.Team1TtlPtsAdj2Selected = false;
        else wagerItem.Team2TtlPtsAdj2Selected = false;
        break;
    }
  };

  function validatePicks() {
    var totalPicks = _ticketService.Ticket.WagerItems.length + _ticketService.Ticket.OpenWagerItems.length;
    var openSpots = _ticketService.GetTotalOpenSpots();
    if (_ticketService.IsClosingOpenPlay() && totalPicks > _ticketService.OpenTotalPicks) {
      _ticketService.DisplayBetSlipError("PLEASE SELECT THE NUMBER OF TEAMS OF YOUR OPEN PLAY");
      $errorHandler.Error($rootScope.ErrorMessage + ' Teaser: ' + _ticketService.Ticket.TeaserName, '_ValidatePicks');
      return false;
    }
    if (!_ticketService.IsClosingOpenPlay() && _ticketService.Ticket.WagerItems.length + (_ticketService.Ticket.KeepOpenPlay ? openSpots : 0) < _ticketService.Ticket.AllowedWagerPicks.MinPicks) {
      _ticketService.DisplayBetSlipError("MINIMUM WAGER PICKS " + (_ticketService.Ticket.AllowedWagerPicks.MinPicks > 1 ? "ARE " : "IS ") + _ticketService.Ticket.AllowedWagerPicks.MinPicks);
      return false;
    } else if (_ticketService.Ticket.WagerItems.length > _ticketService.Ticket.AllowedWagerPicks.MaxPicks) {
      _ticketService.DisplayBetSlipError("MAXIMUM WAGER PICKS " + (_ticketService.Ticket.AllowedWagerPicks.MaxPicks > 1 ? "ARE " : "IS ") + _ticketService.Ticket.AllowedWagerPicks.MaxPicks);
      return false;
    }
      return true;
  };

  function validateWagerItemsAmounts() {
    if (!_ticketService.Ticket.Any()) return false;
    var ret = true;
    if ($wagerTypesService.IsAccumWager()) {
      if (!CommonFunctions.IsNumeric(_ticketService.Ticket.TotalRiskAmount)) {
        ret = false;
      }
      else if (!$wagerTypesService.IsActionReverse() && !CommonFunctions.IsNumeric(_ticketService.Ticket.TotalToWinAmount)) {
        ret = false;
      }
    } else {
      for (var i = 0; i < _ticketService.Ticket.WagerItems.length; i++) {
        var wagerItem = _ticketService.Ticket.WagerItems[i];
        if (!CommonFunctions.IsNumeric(wagerItem.RiskAmt)) {
          ret = false;
          break;
        }
        else if (!CommonFunctions.IsNumeric(wagerItem.ToWinAmt)) {
          ret = false;
          break;
        }
        if (i > 0 && $wagerTypesService.IsIfBet()) {
          var previousWagerItem = _ticketService.Ticket.WagerItems[i - 1];
          //Allan
          //T If Win Only & Win Or Push separation
          if ($customerService.Info.CreditAcctFlag != "Y") {
            if ($wagerTypesService.IsIfBetWinOnly() && (wagerItem.RiskAmt > previousWagerItem.RiskAmt + previousWagerItem.ToWinAmt)) ret = false;
            else if ($wagerTypesService.IsIfBetWinOrPush() && wagerItem.RiskAmt > previousWagerItem.RiskAmt) ret = false;
          }
        }
      }
    }
    if (!ret) {
      _ticketService.DisplayBetSlipError("INVALID_AMOUNT");
    }
    return ret;
  };

  function removeAllWagerItems() {
    _ticketService.ActiveRifWager = null;
    for (var i = _ticketService.Ticket.WagerItems.length - 1; i >= 0; i--) {
      var wi = _ticketService.Ticket.WagerItems[i];
      if (wi.Type == "G") {
        var wagerItemTeamPos = wi.ControlCode.substring(2, 1);
        revertGameWagerSelection(wi.Loo, wi.WagerType, wagerItemTeamPos);
      } else {
        wi.Loo.Selected = false;
      }
      _ticketService.Ticket.WagerItems.splice(i, 1);
      $rootScope.$emit('clearOfferingInput', wi);

    }
  };

  function unSelectAllWagerItems() {
    for (var i = _ticketService.Ticket.WagerItems.length - 1; i >= 0; i--) {
      var wi = _ticketService.Ticket.WagerItems[i];
      var wagerItemTeamPos;
      if (wi.Type == "G") {
        wagerItemTeamPos = wi.ControlCode.substring(2, 1);
        revertGameWagerSelection(wi.Loo, wi.WagerType, wagerItemTeamPos);
      }
      if (wi.Type == "C") {
        wi.Loo.Selected = false;
      }
    }
  };

  function getRoundRobinOptions() {
    if (!$wagerTypesService.IsParlay()) return null;
    _ticketService.Ticket.RoundRobin.Options = ParlayFunctions.GetRoundRobin(_ticketService.Ticket.WagerItems.length, $translatorService);
    _ticketService.Ticket.RoundRobin.Selected = _ticketService.Ticket.RoundRobin.Options[0];
    _ticketService.OpenDisable = false;
    return true;
  };

  function getParlayInfo(parlayName, pickCount = 0) {
    if (!$wagerTypesService.IsParlay()) return null;
    var data = { 'parlayName': parlayName, 'pickCount': pickCount };
    getRoundRobinOptions();
    return _caller.POST(data, 'GetParlayInfo', null, true).then(function (result) {
      _ticketService.Ticket.ParlayInfo = result;
    });
  };

  function getTeaserInfo(teaserName) {
    if (!$wagerTypesService.IsTeaser()) return null;
    var data = {
      'teaserName': teaserName, 'pickCount': 0, 'gamesWon': 0
    };
    return _caller.POST(data, 'GetTeaserInfo', null, true).then(function (result) {
      _ticketService.Ticket.TeaserInfo = result;
      if (result && result.teaserSpecs) {

        var orig = (_ticketService.Ticket.AllowedWagerPicks.MinPicks || 0) + (_ticketService.Ticket.AllowedWagerPicks.MaxPicks || 0);
        _ticketService.Ticket.AllowedWagerPicks.MinPicks = result.teaserSpecs.MinPicks;
        _ticketService.Ticket.AllowedWagerPicks.MaxPicks = result.teaserSpecs.MaxPicks;
        if (orig != (_ticketService.Ticket.AllowedWagerPicks.MinPicks || 0) + (_ticketService.Ticket.AllowedWagerPicks.MaxPicks || 0))
          onWagerPicksChanged();
      }
    });
  };

  function replaceGameWager(wagerItem) {
    wagerItem.Type = "G";
    wagerItem.RiskPlaceHolder = $translatorService.Translate("Risk");
    wagerItem.WinPlaceHolder = $translatorService.Translate("Win");
    wagerItem.RiskAmt = 0;
    wagerItem.ToWinAmt = 0;
    createBuyPointsOptions(wagerItem);
    var found = false;
    for (var i = 0; i < _ticketService.Ticket.WagerItems.length; i++) {
      if (_ticketService.Ticket.WagerItems[i].Loo.GameNum == wagerItem.Loo.GameNum
        && _ticketService.Ticket.WagerItems[i].Loo.PeriodNumber == wagerItem.Loo.PeriodNumber
        && _ticketService.Ticket.WagerItems[i].WagerType == wagerItem.WagerType
        && _ticketService.Ticket.WagerItems[i].ChosenTeamId == wagerItem.ChosenTeamId
        && _ticketService.Ticket.WagerItems[i].ControlCode == wagerItem.ControlCode) {
        _ticketService.Ticket.WagerItems[i] = wagerItem;
        found = true;
        break;
      }
    }
    return found;
  };

  function riskChanged() {
    if (_ticketService.Ticket.WagerItems.length > 0)
      window.WagerAmountOnChange(_ticketService.Ticket.WagerItems[_ticketService.Ticket.WagerItems.length - 1], 'R');
    else if (_ticketService.Ticket.OpenWagerItems.length > 0)
      window.WagerAmountOnChange(_ticketService.Ticket.OpenWagerItems[_ticketService.Ticket.OpenWagerItems.length - 1], 'R');
  };

  _ticketService.StartNewTicket = function () {
    emptyTicket();
    _ticketService.ValidateParlaySelections(true);
    var startNewTicketCall = function () {
      return _caller.POST({ 'wGBS': _ticketService.Ticket.wGBS }, 'New', null, true).then(function () {
        _ticketService.GetWagerPicks().then();
        if (_ticketService.Ticket.OpenWager) {
          setTimeout(function () {
            _ticketService.GetOpenPlaysItems(_ticketService.Ticket.OpenWager);
            _ticketService.Ticket.OpenWager = null;
          }, 1000);
        }
      });
    };
    _ticketService.Ticket.UseFreePlay = false;
    if ($wagerTypesService.IsParlay()) return getParlayInfo(null).then(function () { startNewTicketCall(); });
    else if ($wagerTypesService.IsTeaser()) return getTeaserInfo(_ticketService.Ticket.TeaserName).then(function () { startNewTicketCall(); });
    else return startNewTicketCall().then();
  };

  _ticketService.SyncWithServerDateTime = function () {
    return _caller.POST({}, 'GetServerDateTime', null, true).then(function (result) {
      var sdate = CommonFunctions.SysDate(result);
      var cdate = new Date();
        _ticketService.realDateTime = sdate;
      _ticketService.ServerClienTimeDiff = cdate.getTime() - sdate.getTime();
    });
  }

  _ticketService.GetServerDateTime = function () {
    var cdate = new Date();
    if (_ticketService.ServerClienTimeDiff < 0) cdate.setTime(cdate.getTime() + _ticketService.ServerClienTimeDiff);
    else cdate.setTime(cdate.getTime() - _ticketService.ServerClienTimeDiff);
    //console.log("serverdatetime:", cdate, cdate.getTimezoneOffset() * 60 * 1000);
    return cdate;
    };

  _ticketService.UpdateGameWager = function (wagerItem, isAutoAccept, isFromSocket) {
    wagerItem.Type = "G";
    wagerItem.RiskPlaceHolder = $translatorService.Translate("Risk");
    wagerItem.WinPlaceHolder = $translatorService.Translate("Win");
    var found = false;
    var wi;
    var priceChanged;
    var i;
    for (i = 0; i < _ticketService.Ticket.WagerItems.length; i++) {
      wi = _ticketService.Ticket.WagerItems[i];
      if (wi.Loo.GameNum == wagerItem.Loo.GameNum
        && wi.Loo.PeriodNumber == wagerItem.Loo.PeriodNumber
        && wi.WagerType == wagerItem.WagerType
        && wi.ChosenTeamId == wagerItem.ChosenTeamId
                && wi.ControlCode == wagerItem.ControlCode
                && (!wagerItem.Available || !wagerItem.IsOk || wagerItem.Changed || wagerItem.ChangedInCostumerFavor || _ticketService.Ticket.Posted())) {
        wi.AdjustabeOddsFlag = wagerItem.AdjustabeOddsFlag;
        //wi.AmountEntered = wagerItem.AmountEntered;
        wi.Changed = (wagerItem.Changed || !wagerItem.Available || !wagerItem.IsOk);
        wi.DecimalPrice = wagerItem.DecimalPrice;
        wi.Denominator = wagerItem.Denominator;
        wi.EasternLine = wagerItem.EasternLine;
        wi.EasternLineFlag = wagerItem.EasternLineFlag;
        wi.FinalDecimal = wagerItem.FinalDecimal;
        wi.FinalDenominator = wagerItem.FinalDenominator;
        wi.FinalLine = wagerItem.FinalLine;
        wi.FinalNumerator = wagerItem.FinalNumerator;
        wi.FinalPrice = wagerItem.FinalPrice;
        wi.HalfPointAdded = wagerItem.HalfPointAdded;
        wi.HalfPointValue = wagerItem.HalfPointValue;
        wi.Line = wagerItem.Line;
        wi.MaxWagerLimit = wagerItem.MaxWagerLimit;
        wi.Numerator = wagerItem.Numerator;
        wi.Pitcher1ReqFlag = wagerItem.Pitcher1ReqFlag;
        wi.Pitcher2ReqFlag = wagerItem.Pitcher2ReqFlag;
        wi.PointsBought = wagerItem.PointsBought;
        priceChanged = wi.Price != wagerItem.Price;
        wi.Price = wagerItem.Price;
        wi.RifTicketNumber = wagerItem.RifTicketNumber;
        wi.RifWagerNumber = wagerItem.RifWagerNumber;
        wi.RifWinOnly = wagerItem.RifWinOnly;
        wi.RiskPlaceHolder = wagerItem.RiskPlaceHolder;
        wi.WinPlaceHolder = wagerItem.WinPlaceHolder;
        wi.Available = wagerItem.Available;
        wi.IsOk = wagerItem.IsOk;
        wi.RiskAmt = wagerItem.riskAmt || wagerItem.RiskAmt;
        wi.ToWinAmt = wagerItem.toWinAmt || wagerItem.ToWinAmt;
        wi.PointsBought = wagerItem.PointsBought;
        wi.PointsSold = wagerItem.PointsSold;
        wi.IsBuyingOrSellingPoints = wagerItem.IsBuyingOrSellingPoints;
        wi.ErrorMessage = $translatorService.Translate(wagerItem.ErrorMessage);
          $rootScope.$emit('clearOfferingInput', wi);
        found = true;
        if (wagerItem.Changed && !_ticketService.Ticket.Posted())
            UI.Notify($translatorService.Translate("Line") + ": " + wi.ChosenTeamId + '. ' + $translatorService.Translate("Has changed, please review."), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning, '', 2000);
        break;
      }
    }
    if (!wagerItem.IsExistingOpenItem && found) {
      window.UpdateLineOffering(wagerItem.Loo, wi, isFromSocket);
      if ((!isAutoAccept) && ((!_ticketService.Ticket.Posted() && !wagerItem.ChangedInCostumerFavor) || priceChanged)) {
        wi.RiskAmt = null;
        wi.ToWinAmt = null;
      } else {
        if (priceChanged) {
          $rootScope.$on('buyPointsInfoComplete', function () {
            window.WagerAmountOnChange(wi, wi.AmountEntered == 'ToWinAmount' ? 'W' : 'R');
          });
        } else {
          wi.RiskAmt = wagerItem.RiskAmt > 0 ? CommonFunctions.RoundNumber(wagerItem.RiskAmt) : wi.RiskAmt;
          wi.ToWinAmt = wagerItem.ToWinAmt > 0 ? CommonFunctions.RoundNumber(wagerItem.ToWinAmt) : wi.ToWinAmt;
        }
      }
      $rootScope.safeApply();
    }
    return i;
  };

  _ticketService.syncIfBetWagerItemsLimis = function () {
    if (!$wagerTypesService.IsIfBet() || _ticketService.Ticket.WagerItems.length <= 1) return;
    for (var i = 1; i < _ticketService.Ticket.WagerItems.length; i++) {
      var wi = _ticketService.Ticket.WagerItems[i];
      var pwi = _ticketService.Ticket.WagerItems[i - 1];
      var tempLimit = 0;
      if (wi.OrigMaxWagerLimit) wi.MaxWagerLimit = wi.OrigMaxWagerLimit;
      else wi.OrigMaxWagerLimit = wi.MaxWagerLimit;

      if (pwi.RiskAmt && pwi.ToWinAmt) {
        if ($wagerTypesService.IsIfBetWinOnly()) {
          if (wi.FinalPrice >= 100) tempLimit = (pwi.RiskAmt + pwi.ToWinAmt) * 100;
          else tempLimit = LineOffering.CalculateToWinAmt(pwi.RiskAmt + pwi.ToWinAmt, 'A', wi.FinalPrice) * 100;
        }
        else {
          if (wi.FinalPrice >= 100) tempLimit = (pwi.RiskAmt) * 100;
          else tempLimit = LineOffering.CalculateToWinAmt(pwi.RiskAmt, 'A', wi.FinalPrice) * 100;
        }
        if (tempLimit > 0 && tempLimit < wi.OrigMaxWagerLimit) wi.MaxWagerLimit = tempLimit;
        if (wi.FinalPrice >= 100 && wi.RiskAmt > CommonFunctions.RoundNumber(wi.MaxWagerLimit / 100)) _ticketService.setWagerItemStatus(wi, "Amount Exceeded");
        else if (wi.FinalPrice < 0 && wi.ToWinAmt > CommonFunctions.RoundNumber(wi.MaxWagerLimit / 100)) wi.ErrorMessage = _ticketService.setWagerItemStatus(wi, "Amount Exceeded");
      }
      else {
        wi.RiskAmt = null;
        wi.ToWinAmt = null;
        if (wi.OrigMaxWagerLimit) wi.MaxWagerLimit = wi.OrigMaxWagerLimit;
      }
    }
  };

  _ticketService.setWagerItemStatus = function (wagerItem, errorMsg = null) {
    wagerItem.IsOk = errorMsg == null;
    wagerItem.ErrorMessage = $translatorService.Translate(errorMsg);
    };

  function AddGameWagerItem(gameItem, subWagerType, teamPos, wagerType) {
    if (typeof wagerPos == "undefined") wagerPos = -1;
    if (typeof update == "undefined") update = false;
    _ticketService.Ticket.ArAmount = null;
    function addWagerItemFn() {
      var toWinAmount = 0;
      var riskAmount = 0;
      if ($wagerTypesService.IsAccumWager() && _ticketService.IsClosingOpenPlay()) {
        if ($wagerTypesService.IsTeaser() && gameItem.PeriodNumber > 0) {
          revertGameWagerSelection(gameItem, subWagerType, teamPos);
          return false;
        }
        var maxToEval;
        var amountToEval;
        var totalWagers = (_ticketService.IsClosingOpenPlay() ? _ticketService.OpenTotalPicks : _ticketService.TotalWagers());
        if ($wagerTypesService.IsParlay()) amountToEval = _ticketService.Ticket.TotalRiskAmount;
        else amountToEval = (($wagerTypesService.IsTeaser() && totalWagers > 2) ? _ticketService.Ticket.TotalRiskAmount : _ticketService.Ticket.TotalToWinAmount) * 100;
        if (!_ticketService.IsClosingOpenPlay() && !$wagerTypesService.IsTeaser()) {
        switch (subWagerType) {
          case "S":
            maxToEval = gameItem.CircledMaxWagerSpread && gameItem.CircledMaxWagerSpread != "" && gameItem.CircledMaxWagerSpread < gameItem.SportLimits.MaxWagerSpread ? gameItem.CircledMaxWagerSpread : gameItem.SportLimits.MaxWagerSpread;
              if (maxToEval > amountToEval) {
              UI.Alert($translatorService.Translate("Cannot add this item, game is circled or has a lower limit."));
              revertGameWagerSelection(gameItem, subWagerType, teamPos);
              return false;
            }
            break;
          case "M":
            maxToEval = gameItem.CircledMaxWagerMoneyLine && gameItem.CircledMaxWagerMoneyLine != "" && gameItem.CircledMaxWagerMoneyLine < gameItem.SportLimits.MaxWagerMoneyLine ? gameItem.CircledMaxWagerMoneyLine : gameItem.SportLimits.MaxWagerMoneyLine;
              if (maxToEval > amountToEval) {
              UI.Alert($translatorService.Translate("Cannot add this item, game is circled or has a lower limit."));
              revertGameWagerSelection(gameItem, subWagerType, teamPos);
              return false;
            }
            break;
          case "L":
            maxToEval = gameItem.CircledMaxWagerTotal && gameItem.CircledMaxWagerTotal != "" && gameItem.CircledMaxWagerTotal < gameItem.SportLimits.MaxWagerTotal ? gameItem.CircledMaxWagerTotal : gameItem.SportLimits.MaxWagerTotal;
              if (maxToEval > amountToEval) {
              UI.Alert($translatorService.Translate("Cannot add this item, game is circled or has a lower limit."));
              revertGameWagerSelection(gameItem, subWagerType, teamPos);
              return false;
            }
        }
        }
        if (wagerType.id == $wagerTypesService.Ids.ActionReverse) {

          if (_ticketService.Ticket.WagerItems.length >= 2) {
            UI.Alert($translatorService.Translate("MAX_AR_BET_ITEMS_EXCEEDED"));
            revertGameWagerSelection(gameItem, subWagerType, teamPos);
            return false;
          }

          var currentItem = new Object();
          currentItem.SubWagerType = subWagerType;
          currentItem.Loo = gameItem;

          if (!IfBetFunctions.ValidateIfBetTeamSelection(_ticketService.Ticket.WagerItems, currentItem, wagerType.name, getBlockSTFlags())) {
            UI.Alert($translatorService.Translate("INVALID_BET_SELECTION"));
            revertGameWagerSelection(gameItem, subWagerType, teamPos);
            return false;
          }
        }
      }

      $rootScope.BetSlipLoading = true;

        var _gameItem = gameItem;
      return _caller.POST({
        'subWagerType': subWagerType,
          'gameNumber': _gameItem.GameNum,
          'periodNumber': _gameItem.PeriodNumber,
        'chosenTeamIdx': teamPos,
        'riskAmt': riskAmount,
        'toWinAmt': toWinAmount,
        'wGBS': _ticketService.Ticket.wGBS,
        'isLineUpdate': update,
        'keepOpenPlay': _ticketService.Ticket.KeepOpenPlay || _ticketService.IsClosingOpenPlay()
      }, 'AddToWager', null, true).then(function (addWagerItemFnResult) {
      if (addWagerItemFnResult.ResultCode != ServiceCaller.ResultCode.Success) {
            const index = _ticketService.offeringSelectedItems.findIndex(e => _gameItem.GameNum == e.gameItem.GameNum && _gameItem.ShowDate === e.gameItem.ShowDate && _gameItem.PeriodNumber == e.gameItem.PeriodNumber
              && _gameItem.IsTitle == e.gameItem.IsTitle && e.subWagerType == subWagerType && e.teamPos == teamPos);
        _ticketService.offeringSelectedItems.splice(index, 1);
            revertGameWagerSelection(_gameItem, subWagerType, teamPos);
        _ticketService.DisplayBetSlipError(addWagerItemFnResult.ResultMessage);
        if ($rootScope.IsMobileDevice || !$customerService.Info.ShowBetSlipInWebSite) UI.Alert($rootScope.ErrorMessage);
        $rootScope.BetSlipLoading = false;
        $rootScope.safeApply();
        return false;
      }
      else {
        $rootScope.ErrorMessage = "";
        var openSpots = _ticketService.GetTotalOpenSpots();
        var wagerItem = addWagerItemFnResult;
        wagerItem.Available = true;

            window.updateGameLineData(_gameItem, wagerItem.Loo, wagerItem.WagerType, wagerItem.ControlCode, false);

            wagerItem.Loo = _gameItem;
        if (!replaceGameWager(wagerItem)) {
          _ticketService.Ticket.WagerItems.push(wagerItem);
        }


        if ($wagerTypesService.IsAccumWager()) {
          if (_ticketService.Ticket.KeepOpenPlay && _ticketService.SelectedOpenSpots && openSpots != _ticketService.openPlaysSelection[0].value)
            _ticketService.Ticket.AllowedWagerPicks.OpenPicks = openSpots + _ticketService.TotalWagers();
          if ($wagerTypesService.IsParlay()) getParlayInfo(null).then(function () {
            window.WagerAmountOnChange(wagerItem, 'R');
          });
          else if ($wagerTypesService.IsTeaser()) getTeaserInfo(_ticketService.Ticket.TeaserName).then(function () {
            window.WagerAmountOnChange(wagerItem, 'R');
          });
          _ticketService.syncIfBetWagerItemsLimis();
        }
        if (_ticketService.Ticket.WagerItems.length >= 3 && !$rootScope.IsMobileDevice)
          UI.ScrollDown("betSlipController", "wagerItem_" + wagerItem.ChosenTeamId.RemoveSpecials() + "_" + wagerItem.ControlCode + "_" + wagerItem.Loo.PeriodNumber);

        if ($wagerTypesService.IsTeaser() || $wagerTypesService.IsParlay()) {

          _ticketService.RemoveParentRifWager();

          if (_ticketService.IsClosingOpenPlay() && _ticketService.SelectedOpenSpots) {
            _ticketService.ChangeSelectedOpenSpots(_ticketService.OpenSpotsDropDown[_ticketService.OpenSpotsDropDown.indexOf(_ticketService.SelectedOpenSpots) - 1]);
          } else {
            onWagerPicksChanged();

          }
        }
        $rootScope.BetSlipLoading = false;
        $rootScope.safeApply();
          $rootScope.$broadcast("changeWagerItemsCollection");
        return true;
      }
      });      
    };
    if (_ticketService.Ticket.Posted()) {
      return _ticketService.StartNewTicket().then(function () {
        $rootScope.safeApply();
        return addWagerItemFn();
      });
    } else {
      $rootScope.safeApply();
      return addWagerItemFn();
    }
  };

  _ticketService.GetParlayInfo = function (data) {
    getParlayInfo(data);
  };

  _ticketService.GetTeaserInfo = function (data) {
    if (!data) data = _ticketService.Ticket.TeaserName;
    if (!data) return;
    return getTeaserInfo(data);
  };

  _ticketService.AddContestWagerItem = function (contest, contestantLine) {
    var found = false;
    if (contest == null || contestantLine == null) return false;
    var addContestWagerItemFn = function () {
      return _caller.POST({
        'contestNumber': contestantLine.ContestNum,
        'contestantNumber': contestantLine.ContestantNum,
        'wGBS': _ticketService.Ticket.wGBS
      }, 'AddContestToWager', null, true).then(function (result) {
        var wagerItem = result;
        if (!wagerItem) return null;
        wagerItem.Type = "C";
        wagerItem.Available = true;
        wagerItem.Loo = contestantLine;
        wagerItem.RiskPlaceHolder = $translatorService.Translate("Risk");
        wagerItem.WinPlaceHolder = $translatorService.Translate("Win");
        wagerItem.RiskAmt = null;
        wagerItem.ToWinAmt = null;
        wagerItem.ContestType = (contest && contest.ContestType) ? contest.ContestType : wagerItem.ContestType;
        wagerItem.ContestType2 = (contest && contest.ContestType2) ? contest.ContestType2 : wagerItem.ContestType2;
        wagerItem.ContestType3 = (contest && contest.ContestType3) ? contest.ContestType3 : wagerItem.ContestType3;
        wagerItem.ContestDesc = (contest && contest.ContestDesc) ? contest.ContestDesc : wagerItem.ContestDesc;
        for (var i = 0; i < _ticketService.Ticket.WagerItems.length; i++) {
          if (_ticketService.Ticket.WagerItems[i].Loo.ContestantNum == wagerItem.Loo.ContestantNum && _ticketService.Ticket.WagerItems[i].Loo.ContestNum == wagerItem.Loo.ContestNum) {
            _ticketService.Ticket.WagerItems[i] = wagerItem;
            wagerItem.IsOk = true;
            found = true;
          }
        }
        if (!found) {
          _ticketService.Ticket.WagerItems.push(wagerItem);
          $rootScope.$broadcast("changeWagerItemsCollection");
        }
        if (!$rootScope.IsMobileDevice) UI.ScrollDown("betSlipController");
        return result.ResultCode;
      });
    };

    if (_ticketService.Ticket.Posted())
      return _ticketService.StartNewTicket().then(function () {
        return addContestWagerItemFn();
      });
    else return addContestWagerItemFn();
  };

  _ticketService.RemoveGameWagerItem = function (loo, subWagerType, teamPos, keepUi) {
    if (typeof keepUi === "undefined") keepUi = false;
    return _caller.POST({
      "wGBS": _ticketService.Ticket.wGBS,
      "gameNum": loo.GameNum,
      "periodNumber": loo.PeriodNumber,
      "subWagerType": subWagerType,
      "teamPos": teamPos
    }, 'RemoveFromWager', null, true).then(function () {
      _ticketService.RemoveUiItem(loo, subWagerType, teamPos, keepUi);
      $rootScope.ErrorMessage = "";
    });
  };

  _ticketService.RemoveUiItem = function (loo, subWagerType, teamPos, keepUi) {
    for (var i = 0; i < _ticketService.Ticket.WagerItems.length; i++) {
      var wi = _ticketService.Ticket.WagerItems[i];
      if (wi.Type == "G") {
        var wiTeamPos = wi.ControlCode.substring(2, 1);
        if (wi.Loo.GameNum == loo.GameNum &&
          wi.Loo.PeriodNumber == loo.PeriodNumber &&
          wi.Loo.Store == loo.Store &&
          wi.WagerType == subWagerType &&
          wiTeamPos == teamPos) {
          wi.IsOk = true;
          revertGameWagerSelection(wi.Loo, wi.WagerType, teamPos);
          if (keepUi) _ticketService.Ticket.WagerItems[i].Available = false;
          else _ticketService.Ticket.WagerItems.splice(i, 1);
          if (_ticketService.IsClosingOpenPlay() && _ticketService.IsOpenFull(true)) {
            _ticketService.ChangeSelectedOpenSpots(_ticketService.OpenSpotsDropDown[_ticketService.OpenSpotsDropDown.indexOf(_ticketService.SelectedOpenSpots) + 1]);
          } else {
            if (_ticketService.GetTotalOpenSpots() != _ticketService.openPlaysSelection[0].value)
              _ticketService.Ticket.AllowedWagerPicks.OpenPicks = _ticketService.GetTotalWagersAndOpenSpots();
            onWagerPicksChanged();
          }
          if ($wagerTypesService.IsAccumWager()) {
            if (!_ticketService.IsClosingOpenPlay()) _ticketService.ResetAmounts();
            if ($wagerTypesService.IsParlay())
              getParlayInfo(null).then(function () {
                $rootScope.$broadcast("changeWagerItemsCollection");
                riskChanged();
              });
            else if ($wagerTypesService.IsTeaser())
              getTeaserInfo(_ticketService.Ticket.TeaserName).then(function () {
                $rootScope.$broadcast("changeWagerItemsCollection");
                riskChanged();
              });
          }
          break;
        }
      }
    }
    _ticketService.CalculateTotalAmounts();
  };

  _ticketService.RemoveLocalContestWagerItem = function (contestNum, contestantNum) {
    for (var i = 0; i < _ticketService.Ticket.WagerItems.length; i++) {
      var wagerItem = _ticketService.Ticket.WagerItems[i];
      if (wagerItem.Type == "C" && wagerItem.Loo.ContestNum == contestNum && wagerItem.Loo.ContestantNum == contestantNum) {
        wagerItem.IsOk = true;
        wagerItem.Loo.Selected = false;
        _ticketService.Ticket.WagerItems.splice(i, 1);
        _ticketService.CalculateTotalAmounts();
        return;
      }
    }
  };

  _ticketService.RemoveContestWagerItem = function (contestantLine) {
    return _caller.POST({
      'contestNumber': contestantLine.ContestNum,
      'contestantNumber': contestantLine.ContestantNum,
      'wGBS': _ticketService.Ticket.wGBS
    }, 'RemoveContestFromWager', null, true).then(function () {
      _ticketService.RemoveLocalContestWagerItem(contestantLine.ContestNum, contestantLine.ContestantNum);
      $rootScope.ErrorMessage = "";
    });
  };

  _ticketService.RemoveAllWagerItems = function () {
    return _caller.POST({}, 'EmptyWager', null, true).then(function () {
      removeAllWagerItems();
    });
  };

  _ticketService.Ticket.Any = function () {
    return _ticketService.Ticket.WagerItems.length > 0 || _ticketService.Ticket.OpenWagerItems.length > 0;
  };

  _ticketService.Ticket.Posted = function () {
    return _ticketService.Ticket.TicketNumber != null && _ticketService.Ticket.TicketNumber > 0;
  };

  _ticketService.CalculateMaxRiskAmount = function (wagerItem, tempLimit) {
    if (typeof tempLimit == "undefined") tempLimit = wagerItem.MaxWagerLimit / 100;
    if (wagerItem.Type == "G") {
      var finalPrice = (wagerItem.SelectedLine != null) ? parseInt(wagerItem.SelectedLine.cost) : wagerItem.FinalPrice;
      if (finalPrice < 0 || $wagerTypesService.IsTeaser()) {
        switch ($wagerTypesService.Selected.id) {
          case $wagerTypesService.Ids.StraightBet:
          case $wagerTypesService.Ids.IfWinOrPush:
          case $wagerTypesService.Ids.IfWinOnly:
            tempLimit = CommonFunctions.RoundNumber(LineOffering.CalculateRiskAmtUsingWi(null, tempLimit, 'A'/*wagerItem.PriceType*/, finalPrice));
            break;
          case $wagerTypesService.Ids.Teaser:
            var pc = TeaserFunctions.GetPayCard(_ticketService.Ticket.TeaserInfo.teaserPayCards, _ticketService.Ticket.lowestWager.length);
            if (pc != null) {
              var tempRiskLimit = TeaserFunctions.CalculateRisk(pc, tempLimit);
              if (tempRiskLimit > tempLimit) tempLimit = tempRiskLimit;
            }
            break;
        }
      }
    }
    return tempLimit;
  };

  _ticketService.CalculateMaxToWinAmount = function (wagerItem) {
    var lowestWager = wagerItem;
    if ($wagerTypesService.IsStraightBet() || $wagerTypesService.IsIfBet())
      _ticketService.Ticket.WagerItems.forEach(function (wager) {
        if (wager.MaxWagerLimit < lowestWager.MaxWagerLimit)
          lowestWager = wager;
      });
    var tempLimit = (lowestWager.MaxWagerLimit ? lowestWager.MaxWagerLimit : 0) / 100;
    if (lowestWager.Type == "G") {
      var finalPrice = (lowestWager.SelectedLine != null) ? parseInt(lowestWager.SelectedLine.cost) : lowestWager.FinalPrice;
      if (finalPrice < 0 || $wagerTypesService.IsTeaser()) {
        switch ($wagerTypesService.Selected.id) {
          case $wagerTypesService.Ids.IfWinOrPush:
          case $wagerTypesService.Ids.IfWinOnly:
          case $wagerTypesService.Ids.StraightBet:
            tempLimit = CommonFunctions.RoundNumber(LineOffering.CalculateToWinAmtUsingWi(null, tempLimit, lowestWager.PriceType, finalPrice));
            break;
          case $wagerTypesService.Ids.Parlay:
            var roundRobin = _ticketService.GetSelectedRoundRobin();
            if (roundRobin == null) {
              tempLimit = ParlayFunctions.CalculateParlayToWinAmt(_ticketService.Ticket.WagerItems, _ticketService.Ticket.ParlayInfo, ParlayFunctions.GetPayCardMaxPayout(_ticketService.Ticket.WagerItems.length, _ticketService.Ticket.ParlayInfo, tempLimit), tempLimit);
            }
            else {
              var rrValues = ParlayFunctions.CalculateRoundRobinToWin(_ticketService.Ticket.WagerItems, _ticketService.Ticket.ParlayInfo, tempLimit, roundRobin.value, $customerService.Info.RoundRobinMaxPayout);
              tempLimit = rrValues.ToWinAmt;
            }
            break;
          case $wagerTypesService.Ids.Teaser:
            var pc = TeaserFunctions.GetPayCard(_ticketService.Ticket.TeaserInfo.teaserPayCards, _ticketService.Ticket.WagerItems.length);
            if (pc != null) {
              var tempWinLimit = TeaserFunctions.CalculateToWin(pc, tempLimit);
              if (tempWinLimit > tempLimit) tempLimit = tempWinLimit;
            }
            break;
        }
      }
    }
    return tempLimit;
  };

  _ticketService.CalculateTotalAmounts = function () {
    if ($wagerTypesService.Selected.id == $wagerTypesService.Ids.Teaser
      || $wagerTypesService.Selected.id == $wagerTypesService.Ids.Parlay
      || !_ticketService.Ticket.WagerItems
      || !_ticketService.Ticket.WagerItems.length) return;
    var totalRisk = 0, totalToWin = 0;
    for (var i = 0; i < _ticketService.Ticket.WagerItems.length; i++) {
      var wi = _ticketService.Ticket.WagerItems[i];
      totalRisk += (isNaN(wi.RiskAmt) || wi.RiskAmt == "" ? 0 : CommonFunctions.RoundNumber(wi.RiskAmt, false));
      totalToWin += (isNaN(wi.ToWinAmt) || wi.ToWinAmt == "" ? 0 : CommonFunctions.RoundNumber(wi.ToWinAmt, false));
    }
    _ticketService.Ticket.TotalToWinAmount = totalToWin;
    switch ($wagerTypesService.Selected.id) {
      case $wagerTypesService.Ids.IfWinOnly:
        var totalToWinIfBet = 0;
          var ifBetCalc = _ticketService.Ticket.WagerItems[0].RiskAmt || 0;
        for (var j = 1; j < _ticketService.Ticket.WagerItems.length; j++) {
          var currentRisk = parseFloat(_ticketService.Ticket.WagerItems[j].RiskAmt);
          totalToWinIfBet += CommonFunctions.RoundNumber(_ticketService.Ticket.WagerItems[j - 1].ToWinAmt || 0, false);
          if (currentRisk > totalToWinIfBet && ifBetCalc < (currentRisk - totalToWinIfBet)) {
            ifBetCalc = currentRisk - totalToWinIfBet;
          }
        }
        _ticketService.Ticket.TotalRiskAmount = ifBetCalc;
        break;
      case $wagerTypesService.Ids.IfWinOrPush:
        var highestRisk = 0;
        _ticketService.Ticket.WagerItems.forEach(function (val) {
          if (val.RiskAmt > highestRisk) highestRisk = val.RiskAmt;
        });
        _ticketService.Ticket.TotalRiskAmount = highestRisk;
        break;
      case $wagerTypesService.Ids.StraightBet:
        _ticketService.Ticket.TotalRiskAmount = totalRisk;
        break;
    }
  };

  _ticketService.SportHasWagersSelected = function (sportType, sportSubType) {
    if (_ticketService.Ticket.Posted()) return false;
    for (var i = 0; i < _ticketService.Ticket.WagerItems.length; i++) {
      var wagerItem = _ticketService.Ticket.WagerItems[0];
      if (wagerItem.Loo.SportType == sportType && wagerItem.Loo.SportSubType == sportSubType) return true;
    }
    return false;
  };

    _ticketService.ProcessTicket = function () {
    if (!validatePicks() || !validateWagerItemsAmounts()) return false;
    var j;
    var wagerItemsData = prepareWagerData();
    _ticketService.TicketProcessed = false;
    _ticketService.PlacingBet = true;
      var openPlayTotalPicks = _ticketService.GetTotalOpenSpots();

    return _caller.POST({
        'wGBS': _ticketService.Ticket.wGBS,
        'password': _ticketService.Ticket.Password,
        'useFreePlay': _ticketService.Ticket.UseFreePlay,
        'wagersData': wagerItemsData,
        'openPlayTotalPicks': openPlayTotalPicks,
        'teaserName': _ticketService.Ticket.TeaserName,
        'arbc': _ticketService.Ticket.ARBC,
        'wagerTypeId': $wagerTypesService.Selected.id
    }, 'ProcessTicket').then(function (result) {
      _ticketService.TicketProcessed = true;
      _ticketService.PlacingBet = false;
      var wi;
      if (!$rootScope.IsWebSocketSupported()) $errorHandler.Error("Socket " + $rootScope.GetCurrentSocketServer() + " is not supported by browser. State: " + $rootScope.GetWebSocketState(), 'ProcessTicket');
      if (result.ResultCode == 0 && result.TicketNumber && result.TicketNumber > 0) {
        _ticketService.Ticket.TicketNumber = result.TicketNumber;
        if (result && result.GameWagerItems)
          for (j = 0; j < result.GameWagerItems.length; j++) {
            wi = result.GameWagerItems[j];
            _ticketService.WagerAvailable(wi, _ticketService.UpdateGameWager(wi, true, false));
          }
        unSelectAllWagerItems();
        $rootScope.ErrorMessage = "";
        _ticketService.OpenPlays = [];
        _ticketService.IsMoverReady = false;
        _ticketService.Ticket.ArAmount = null;
        _ticketService.ActiveRifWager = null;
        $customerService.GetCustomerInfo();
        setTimeout(function () {
          $('#betSlipBody').animate({
            scrollTop: $('#betSlipBody').scrollTop() + $('#alertSuccess').offset().top - 100
          }, 'fast');
        }, 200);
        _ticketService.offeringSelectedItems = [];
         return result;
      } else {
        _ticketService.DisplayBetSlipError(result.ResultMessage);
        if (!_ticketService.IsClosingOpenPlay() && $wagerTypesService.IsAccumWager()) {
          _ticketService.Ticket.TotalRiskAmount = null;
          _ticketService.Ticket.RRTotalRiskAmount = null;
          _ticketService.Ticket.TotalToWinAmount = null;
          _ticketService.Ticket.ArAmount = null;
        }
        switch (result.ResultCode) {
          case 4:
            if (result && result.WagerPos) {
              if (result.ResultMessage.indexOf('changed') > 0) {

                _ticketService.Ticket.WagerItems[result.WagerPos - 1].Changed = true;
                setTimeout(function () { _ticketService.Ticket.WagerItems[result.WagerPos - 1].Changed = false; }, 30000);
              }
            }
            for (i = 0; i < _ticketService.Ticket.WagerItems.length; i++) {
              wi = _ticketService.Ticket.WagerItems[i];
              if (result.WagerOrContestItem && result.WagerOrContestItem.WagerItem)
                if (wi.Loo.GameNum == result.WagerOrContestItem.WagerItem.Loo.GameNum)
                  wi.IsOk = false;
              if (result.WagerOrContestItem && result.WagerOrContestItem.ContestItem)
                if (wi.Loo.ContestNum == result.WagerOrContestItem.ContestItem.ContestNum)
                  wi.IsOk = false;
            }
            break;
          case 1:
          case 5:
            setTimeout(function () {
              $('#betSlipBody').animate({
                scrollTop: 9999
              }, 'fast');
            }, 200);
            return;
          case 6:
            UI.Alert(result.ResultMessage, 'Warning', function () {
              $rootScope.Logout();
            });
            break;
        }
        //if (result && result.GameWagerItems && result.data.d.Message.indexOf('changed') >= 0)
        for (j = 0; j < result.GameWagerItems.length; j++) {
          wi = result.GameWagerItems[j];
          if (wi.Changed || !wi.Available || !wi.IsOk) {
            UI.ScrollDown('betSlipController', 'wagerItem_' + wi.ChosenTeamId.RemoveSpecials() + '_' + wi.ControlCode);
          }
          _ticketService.WagerAvailable(wi, _ticketService.UpdateGameWager(wi, $customerService.AutoAccept, false));
        }
        setTimeout(function () {
          $('#betSlipBody').animate({
            scrollTop: 9999
          }, 'fast');
        }, 200);
      }
    });
  };

  _ticketService.WagerAvailable = function (wager) {
    if (wager.IsExistingOpenItem) return true;
    var isAvailable = wager.Available;
    var typeName = "";
    if (wager.Type == "C") {
      return false; //wager.Loo.LineChanged || wager.Changed;
    }
    var wagerSubType = wager.ControlCode.substring(0, 1);
    switch (wagerSubType) {
      case "M":
        isAvailable = isAvailable && wager.Loo.MoneyLine1 != null && wager.Loo.MoneyLine2 != null ? true : false;
        typeName = "Money Line";
        break;
      case "S":
        isAvailable = isAvailable && wager.Loo.Spread1 != null && wager.Loo.Spread2 != null ? true : false;
        typeName = "Spread";
        break;
      case "E":
        isAvailable = isAvailable && wager.Loo.Team1TtlPtsAdj1 != null && wager.Loo.Team1TtlPtsAdj2 != null && wager.Loo.Team2TtlPtsAdj1 != null && wager.Loo.Team2TtlPtsAdj2 != null ? true : false;
        typeName = "Team Total";
        break;
      case "L":
        isAvailable = isAvailable && wager.Loo.TtlPtsAdj1 != null && wager.Loo.TtlPtsAdj2 != null ? true : false;
        typeName = "Total";
        break;
      default:
        isAvailable = false;
    }
    if (!isAvailable) {
      UI.Notify($translatorService.Translate("Line") + ": " + wager.ChosenTeamId + "/" + $translatorService.Translate(typeName) + " " +
        $translatorService.Translate("Is not available any more"), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
      _ticketService.RemoveGameWagerItem(wager.Loo, wager.WagerType, wager.ControlCode.substring(2, 1), true).then();
    }
    return isAvailable;
  };

  _ticketService.GetSelectedRoundRobin = function () {
    if (_ticketService.Ticket.RoundRobin == null ||
      _ticketService.Ticket.RoundRobin.Options == null ||
      _ticketService.Ticket.RoundRobin.Selected == null ||
      _ticketService.Ticket.RoundRobin.Selected == _ticketService.Ticket.RoundRobin.Options[0]) return null;
    return _ticketService.Ticket.RoundRobin.Selected;
  };

  _ticketService.ResetAmounts = function (wagerItem) {
    if (wagerItem != null) {
      wagerItem.RiskAmt = 0;
      wagerItem.ToWinAmt = 0;
      if (wagerItem.SelectedLine != null) {
        wagerItem.FinalPrice = parseInt(wagerItem.SelectedLine.cost);
        wagerItem.FinalLine = parseInt(wagerItem.SelectedLine.points);
      }
    } else {
      _ticketService.Ticket.TotalRiskAmount = 0;
      _ticketService.Ticket.RRTotalRiskAmount = 0;
      _ticketService.Ticket.TotalToWinAmount = 0;
      _ticketService.Ticket.ArAmount = 0;
    }
  };

  function onWagerPicksChanged(wagerPicks) {
        var totalWagersPick = _ticketService.TotalWagers();
        var elements = _ticketService.Ticket.AllowedWagerPicks.MaxPicks - totalWagersPick + 1;
        _ticketService.OpenSpotsDropDown = [];
        for (var j = 0; j < elements && j < _ticketService.openPlaysSelection.length; j++) {
          _ticketService.OpenSpotsDropDown.push(_ticketService.openPlaysSelection[j]);
        }
        if (!_ticketService.IsClosingOpenPlay()) {
          _ticketService.ChangeSelectedOpenSpots(_ticketService.OpenSpotsDropDown[0]);
        }
    };

  _ticketService.GetWagerPicks = function () {

    return _caller.POST({}, 'GetWagerPicks').then(function (result) {
      var wagerPicks = result;
      if (wagerPicks != null) {
        var orig = (_ticketService.Ticket.AllowedWagerPicks.MinPicks || 0) + (_ticketService.Ticket.AllowedWagerPicks.MaxPicks || 0);
        _ticketService.Ticket.AllowedWagerPicks.MinPicks = (wagerPicks.MinPicks <= 0 && ($wagerTypesService.IsTeaser() || $wagerTypesService.IsParlay()) ? 2 : wagerPicks.MinPicks);
        _ticketService.Ticket.AllowedWagerPicks.MaxPicks = (wagerPicks.MaxPicks <= 0) ? 999 : wagerPicks.MaxPicks;
        if (orig != (_ticketService.Ticket.AllowedWagerPicks.MinPicks || 0) + (_ticketService.Ticket.AllowedWagerPicks.MaxPicks || 0))
          onWagerPicksChanged();
      }
    });


  };

  _ticketService.GetOpenPlays = function () {
    return _caller.POST({}, 'GetOpenPlays').then(function (result) {
      _ticketService.OpenPlays = result;
      var wagerType = ($wagerTypesService.Selected.id == 1 ? 'Parlay' : 'Teaser');
      _ticketService.OpenPlays.forEach(function (part) {
        part.OpenName = part.TotalPicks + ' ' + $translatorService.Translate('Teams') + ' ' + $translatorService.Translate(wagerType);
      });
      $rootScope.$broadcast("OpenPlaysLoaded");
    });
  };

  _ticketService.ChangeTeaserName = function (teaserName) {
    if (!teaserName) return;
    _ticketService.Ticket.TeaserName = teaserName;
    getTeaserInfo(_ticketService.Ticket.TeaserName);
  };

  _ticketService.GetOpenPlaysItems = function (openWager) {
    if (!openWager) return;
    _ticketService.Ticket.TotalRiskAmount = openWager.AmountWagered / 100;
    _ticketService.Ticket.TotalToWinAmount = openWager.ToWinAmount / 100;
    _ticketService.ChangeTeaserName(openWager.TeaserName);
    _ticketService.OpenTotalPicks = openWager.totalPicks;
    _ticketService.Ticket.OpenWagerItems = [];
    _ticketService.Ticket.TicketNumber = null;
    var groupedItems = null;
    var holdTicketNumber = null;
    var holdWagerNumber = null;
    var callerOpen = new ServiceCaller($http, 'reports');
    //var getOpenPlays = function () {
    callerOpen.POST({ 'ticketNumber': openWager.TicketNumber, 'wagerNumber': openWager.WagerNumber, 'wGBS': _ticketService.Ticket.wGBS }, 'GetWagerItemsOpenPlays').then(function (result) {
      var allOpenBets = result;
      var groupedOpenBets = new Array();
      if (allOpenBets != null && allOpenBets.length > 0) {
        groupedOpenBets = new Array();
        groupedItems = new Array();
        holdTicketNumber = allOpenBets[0].TicketNumber;
        holdWagerNumber = allOpenBets[0].WagerNumber;
        for (var i = 0; i < allOpenBets.length; i++) {
          allOpenBets[i].Available = true;
          if (holdTicketNumber != allOpenBets[i].TicketNumber || holdWagerNumber != allOpenBets[i].WagerNumber) {
            groupedOpenBets.push(allOpenBets[i - 1]);
            if (groupedOpenBets.length > 0 && groupedItems != null && groupedItems.length > 0)
              groupedOpenBets[groupedOpenBets.length - 1].Items = groupedItems;
            groupedItems = new Array();
            groupedItems.push(newWagerItem(allOpenBets[i]));
          } else {
            groupedItems.push(newWagerItem(allOpenBets[i]));
          }
          holdTicketNumber = allOpenBets[i].TicketNumber;
          holdWagerNumber = allOpenBets[i].WagerNumber;

          if (i == allOpenBets.length - 1) {
            groupedOpenBets.push(newWagerItem(allOpenBets[i]));
            groupedOpenBets[groupedOpenBets.length - 1].Items = groupedItems;
          }
        }
      }
      if (groupedOpenBets && groupedOpenBets.length > 0)
        for (var j = 0; j < groupedOpenBets[0].Items.length; j++) {
          groupedOpenBets[0].Items[j].FinalPrice = groupedOpenBets[0].Items[j].FinalLine;
          groupedOpenBets[0].Items[j].Type = 'G';
          groupedOpenBets[0].Items[j].Loo = groupedOpenBets[0].Items[j];
          _ticketService.Ticket.OpenWagerItems.push(groupedOpenBets[0].Items[j]);
        }
      _ticketService.OpenSpotsDropDown = [];
      _ticketService.Ticket.AllowedWagerPicks.OpenPicks = openWager.totalPicks - _ticketService.TotalWagers();
      for (j = 0; j <= _ticketService.Ticket.AllowedWagerPicks.OpenPicks && j < _ticketService.openPlaysSelection.length; j++) {
        _ticketService.OpenSpotsDropDown.push(_ticketService.openPlaysSelection[j]);
      };
      _ticketService.ChangeSelectedOpenSpots(_ticketService.OpenSpotsDropDown[_ticketService.OpenSpotsDropDown.length - 1]);
      _ticketService.TicketProcessed = true;
    });
  };

  _ticketService.IsClosingOpenPlay = function () {
    return _ticketService.Ticket.OpenWagerItems.length > 0;
  };

  _ticketService.IsOpenFull = function () {
    var isOpen = _ticketService.IsClosingOpenPlay();
    if (!isOpen) _ticketService.ShowOpenPlayItems = false;
    var isFull = (isOpen && _ticketService.OpenTotalPicks >= _ticketService.TotalWagers() + 1) || (!isOpen && _ticketService.Ticket.AllowedWagerPicks.OpenPicks >= _ticketService.TotalWagers() + 1);
    if (isFull) _ticketService.Ticket.KeepOpenPlay = false;
    return isFull;
  };

  /*_ticketService.GetTeaserInfo = function (teaserName) {
    return getTeaserInfo(teaserName);
  };*/

  _ticketService.GetOpenPlay = function (wagerToOpen) {
    _ticketService.Ticket.OpenWager = wagerToOpen;
    $wagerTypesService.Selected = wagerToOpen.WagerType == 'P' ? $wagerTypesService.List[1] : $wagerTypesService.List[2];
  };

  _ticketService.TotalWagers = function () {
    var wagerCount = 0;
    _ticketService.Ticket.WagerItems.forEach(function (a) {
      if (!a.Available == false) wagerCount++;
    });
    return _ticketService.Ticket.OpenWagerItems.length + wagerCount;
  };

  _ticketService.GetTotalOpenSpots = function () {
    if (!_ticketService.SelectedOpenSpots || !_ticketService.SelectedOpenSpots.value) return 0;
    if (_ticketService.SelectedOpenSpots.value >= 999) return 0;
    return _ticketService.SelectedOpenSpots.value;
  };

  _ticketService.GetTotalWagersAndOpenSpots = function () {
    return _ticketService.TotalWagers() + _ticketService.GetTotalOpenSpots();
  };

  _ticketService.UnSelectAllWagerItems = function () {
    return unSelectAllWagerItems();
  };

  _ticketService.ChangeSelectedOpenSpots = function (val) {
    if (!val) return;
    _ticketService.SelectedOpenSpots = val;
    if (val.value >= _ticketService.OpenSpotsDropDown.length) {
      _ticketService.Ticket.KeepOpenPlay = false;
      _ticketService.Ticket.AllowedWagerPicks.OpenPicks = 999;
    } else {
      if (_ticketService.Ticket.RoundRobin.Options && _ticketService.Ticket.RoundRobin.Selected != _ticketService.Ticket.RoundRobin.Options[0]) {
        _ticketService.Ticket.RoundRobin.Selected = _ticketService.Ticket.RoundRobin.Options[0];
        UI.Notify($translatorService.Translate("OPEN SPOTS ARE ONLY AVAILABLE FOR SINGLE PARLAYS"), UI.Position.Top, UI.Position.Center, 200, UI.Type.Info);
      }
      _ticketService.Ticket.KeepOpenPlay = _ticketService.Ticket.AllowedWagerPicks.OpenPicks > _ticketService.TotalWagers();
      _ticketService.Ticket.AllowedWagerPicks.OpenPicks = _ticketService.GetTotalWagersAndOpenSpots();
    }
  };

  _ticketService.Continue = function () {
    if ($rootScope.SetPassword) _ticketService.IsMoverReady = true;
    var wagerItemsData = prepareWagerData();
    return _caller.POST({ 'wagersData': wagerItemsData }, 'Continue').then(function (result) {
      if (result.ResultCode == 0) _ticketService.IsMoverReady = true;
    });
  };

  _ticketService.CreateBuyPointsOptions = function (wi) {
    createBuyPointsOptions(wi);
  };

  _ticketService.DisplayBetSlipError = function (msg) {
    $rootScope.ErrorMessage = $translatorService.Translate(msg);
    UI.ScrollDown("betSlipController", "errorMessage");
    };

  _ticketService.GetParlayLimit = function () {
    var limits = _ticketService.Ticket.ParlayInfo.ParlayLimits;
    var totalSelections = _ticketService.GetTotalWagersAndOpenSpots();
    if (totalSelections < 2 || totalSelections > 100) totalSelections = 2;
    var limit = limits.find(l => l.Teams == totalSelections);
    if (!limit) return 0;
    return limit.InetLimit;
    };

  _ticketService.AddParentRifWager = function (openWager, rifWinOnlyFlag, wagerItem) {
    _ticketService.Ticket.UseFreePlay = false;

    var ticketNumber = openWager.TicketNumber;
    var wagerNumber = openWager.WagerNumber;
    var toWinAmount = openWager.ToWinAmount;
    var amountWagered = openWager.AmountWagered;
    var wagerLimit = 0;

    if (wagerItem.FinalPrice < 0) {
      wagerLimit = !rifWinOnlyFlag ? amountWagered : amountWagered + openWager.ToWinAmount;
      wagerLimit = LineOffering.CalculateToWinAmt(wagerLimit, 'A', wagerItem.FinalPrice);
    }
    else
      wagerLimit = !rifWinOnlyFlag ? amountWagered : amountWagered + openWager.ToWinAmount;

    if (wagerItem) {
      wagerItem.RifTicketNumber = ticketNumber;
      wagerItem.RifWagerNumber = wagerNumber;
      wagerItem.RifRiskAmount = toWinAmount / 100;
      //wagerItem.RiskAmt = riskAmount / 100;
      wagerItem.RifWinOnlyFlag = rifWinOnlyFlag;
      wagerItem.OrigMaxWagerLimit = wagerItem.MaxWagerLimit;
      if (wagerLimit > 0 && wagerLimit < wagerItem.MaxWagerLimit) wagerItem.MaxWagerLimit = wagerLimit;
    }
    if ($wagerTypesService.IsStraightBet() && wagerItem) return;
    var volume = toWinAmount < amountWagered ? toWinAmount : amountWagered;
    if (wagerLimit > 0 && wagerLimit > volume) wagerLimit = volume;
    _ticketService.Ticket.ParentRifWager = {
      TicketNumber: ticketNumber,
      WagerNumber: wagerNumber,
      RiskAmount: toWinAmount / 100,
      RifWinOnlyFlag: rifWinOnlyFlag,
      MaxWagerLimit: wagerLimit
    };
    //_ticketService.Ticket.TotalRiskAmount = riskAmount / 100;
  };

  _ticketService.RemoveParentRifWager = function (wagerItem) {
    if (!wagerItem) wagerItem = _ticketService.Ticket.WagerItems[0];
    if (wagerItem) {
      wagerItem.RifTicketNumber = 0;
      wagerItem.RifWagerNumber = 0;
      wagerItem.RifRiskAmount = null;
      if (wagerItem.OrigMaxWagerLimit)
        wagerItem.MaxWagerLimit = wagerItem.OrigMaxWagerLimit;
    }
    _ticketService.Ticket.ParentRifWager = {
      TicketNumber: 0,
      WagerNumber: 0,
      RiskAmount: null,
      MaxWagerLimit: null
    };
  };

  _ticketService.GetParentRif = function (wagerItem) {

    if (wagerItem && $wagerTypesService.IsStraightBet()) {
      return {
        RifTicketNumber: wagerItem.RifTicketNumber,
        RifWagerNumber: wagerItem.RifWagerNumber,
        RifRiskAmount: wagerItem.RifAmountWagered
      };
    }
    return {
      RifTicketNumber: _ticketService.Ticket.ParentRifWager.TicketNumber,
      RifWagerNumber: _ticketService.Ticket.ParentRifWager.WagerNumber,
      RifRiskAmount: _ticketService.Ticket.ParentRifWager.RiskAmount
    };

  }

  _ticketService.IsRif = function (wagerItem) {
    if (wagerItem && $wagerTypesService.IsStraightBet()) return !!wagerItem.RifTicketNumber;
    return !$wagerTypesService.IsStraightBet() && !!_ticketService.Ticket.ParentRifWager.TicketNumber;
  };

  _ticketService.IsAsian = function (points) {
    if (!points) return false;
    var ah = Math.abs(points) - (Math.abs(~~points));
    return (ah == 0.25 || ah == 0.75);
  };

  _ticketService.IsAnyWagerAsian = function () {
    for (i = 0; i < _ticketService.Ticket.WagerItems.length; i++) {
      var wi = _ticketService.Ticket.WagerItems[i];
      if (_ticketService.IsAsian(wi.FinalLine)) {
        return true;
      }
    }
    return false;
  };

  _ticketService.CheckForInvalidRifCombinations = function (ticketNumber, wagerNumber, sessionWagerIndex) {
    return _caller.POST({ ticketNumber: ticketNumber, wagerNumber: wagerNumber, sessionWagerIndex: sessionWagerIndex }, 'CheckForInvalidRifCombinations', null, true).then();
  };

  _ticketService.GradingWagerEarlyPayout = function (ticketNumber, wagerNumber) {
    return _caller.POST({ 'ticketNumber': ticketNumber, 'wagerNumber': wagerNumber }, 'GradingWagerEarlyPayout').then();
  };

  _ticketService.GradingWagerEarlyPayoutCalculateToWin = function (ticketNumber, wagerNumber) {
    return _caller.POST({ 'ticketNumber': ticketNumber, 'wagerNumber': wagerNumber }, 'GradingWagerEarlyPayoutCalculateToWin').then();
  };

  _ticketService.AddGameWagerItem = AddGameWagerItem;

  _ticketService.GameLineAction = GameLineAction;

  return _ticketService;

}]);
;
appModule.factory('$sportsAndContestsService', ['$http', '$rootScope', '$wagerTypesService', '$ticketService', '$customerService', '$translatorService', function ($http, $rootScope, $wagerTypesService, $ticketService, $customerService, $translatorService) {

  var _caller = new ServiceCaller($http, 'Offering');
  var _sportsAndContestsService = {};

  _sportsAndContestsService.SportsAndContests = [];
  _sportsAndContestsService.Selections = [];

  //Private Methods

  function removeContestant(selection, contestNum, contestantNum) {
    for (var i = 0; i < selection.ContestantsLines.length; i++) {
      var contestant = selection.ContestantsLines[i];
      if (contestant.ContestNum == contestNum && contestant.ContestantNum == contestantNum) {
        selection.ContestantsLines.splice(i, 1);
        return;
      }
    }
  }

  function restoreContestantChangedLine(contestant) {
    setTimeout(function () {
      contestant.LineChanged = false;
      $rootScope.safeApply();
    }, 30000);
  };

  function updateContestantLineData(c, cl) {
    if (c.MoneyLine != cl.MoneyLine) {
      c.MoneyLine = cl.MoneyLine;
      c.Decimal = cl.DecimalOdds;
      c.Numerator = cl.Numerator;
      c.Denominator = cl.Denominator;
      c.LineChanged = true;
    }
    if (c.LineChanged)
      restoreContestantChangedLine(c);
  };

  function contestLineUpdate(lChanged, selection) {
    var wt = $wagerTypesService.Selected;
    var shadeLineFound = false;
    for (var a = 0; a < selection.ContestantsLines.length; a++) {
      if (selection.ContestantsLines[a].ContestantNum == lChanged.ContestantNum) {
        if (selection.ContestantsLines[a].CustProfile.trim() == lChanged.CustProfile.trim()) {
          if (lChanged.Status == "H") {
            selection.ContestantsLines.splice(a, 1);
            for (var b = 0; b < $ticketService.Ticket.WagerItems.length; b++) {
              var wagerItem = $ticketService.Ticket.WagerItems[b];
              if (wagerItem.Type == "C" && wagerItem.Loo.ContestantNum == lChanged.ContestantNum) {
                wagerItem.Loo.Selected = false;
                $ticketService.RemoveContestWagerItem(wagerItem.Loo, b);
                $ticketService.Ticket.WagerItems.splice(b, 1);
                $ticketService.CalculateTotalAmounts();
              }
            }
            if (selection.ContestType3 != ".") {
              for (var k = 0; k < _sportsAndContestsService.Selections.length; k++) {
                if (_sportsAndContestsService.Selections[k].ContestType2 == lChanged.ContestType2 && _sportsAndContestsService.Selections[k].ContestType3 == lChanged.ContestType3) {
                  _sportsAndContestsService.Selections.splice(k, 1);
                  break;
                }
              };
            }
            $ticketService.CalculateTotalAmounts();
            break;
          } else {
            _caller.POST({ 'newItem': lChanged, 'eventOffering': 'C', 'wagerType': wt.name }, 'ProcessLineChange', null, true).then(function (result) {
              var contest = result != null && result.NLoo != null ? result.NLoo : null;
              if (contest != null) updateContestantLineData(selection.ContestantsLines[a], contest.ContestantsLines[0]);
              else removeContestant(selection, lChanged.GameNum, lChanged.ContestantNum);
              if (!$ticketService.Ticket.Posted()) {
                $ticketService.RemoveLocalContestWagerItem(lChanged.GameNum, lChanged.ContestantNum);
              }
              $rootScope.safeApply();
            });
            return true;
          }

        } else {
          if (selection.ContestantsLines[a].CustProfile.trim() == CommonFunctions.DefaultCustProfile) {
            selection.ContestantsLines[a].disabled = true;
          } else
            shadeLineFound = true;
        }
      }

      if (a == selection.ContestantsLines.length - 1 && lChanged.Status != "H") {
        _caller.POST({ 'newItem': lChanged, 'eventOffering': 'C', 'wagerType': wt.name }, 'ProcessLineChange', null, true).then(function (result) {
          var contestant = result.NLoo.ContestantsLines[0];
          contestant.disabled = contestant.CustProfile.trim() == CommonFunctions.DefaultCustProfile && shadeLineFound;
          contestant.isTitle = false;
          selection.ContestantsLines.push(contestant);
          $rootScope.safeApply();
        });
        return false;
      };
    };
    return true;
  }

  function isIfBetWagerItem(gameNum, periodNumber, wt) {
    if (wt.code == LineOffering.WTIfWinPush || wt.code == LineOffering.WTIfWin) {
      var found = false;

      angular.forEach(_IfBetItems, function (wi) {
        if (wi.Loo.GameNum == gameNum && wi.Loo.PeriodNumber == periodNumber) {
          found = true;
          return found;
        }
        return false;
      });
      return found;
    } else return false;
  };

  function isCircledVisible(gl) {

    if (gl.CircledMaxWagerSpreadType == "H" || gl.CircledMaxWagerSpreadType == "L" || gl.CircledMaxWagerMoneyLineType == "H" ||
      gl.CircledMaxWagerMoneyLineType == "L" || gl.CircledMaxWagerTotalType == "H" || gl.CircledMaxWagerTotalType == "L" || gl.CircledMaxWagerTeamTotalType == "H" ||
      gl.CircledMaxWagerTeamTotalType == "L") return true;
    return false;
  };

  function getLineChangeStyle(wagerType, gl, newGl) {

    var line1ChangeStyle, line2ChangeStyle;


    switch (wagerType) {
      case 'S':

        if (gl.Spread1 > newGl.Spread1) {
          line1ChangeStyle = 'lc-red';
          line2ChangeStyle = 'lc-green';
        } else if (gl.Spread1 < newGl.Spread1) {
          line1ChangeStyle = 'lc-green';
          line2ChangeStyle = 'lc-red';
        } else if (gl.SpreadAdj1 > newGl.SpreadAdj1) {
          line1ChangeStyle = 'lc-red';
          line2ChangeStyle = 'lc-green';
        } else if (gl.SpreadAdj1 < newGl.SpreadAdj1) {
          line1ChangeStyle = 'lc-green';
          line2ChangeStyle = 'lc-red';
        }

        break;
      case 'M':

        if (gl.MoneyLine1 > newGl.MoneyLine1) {
          line1ChangeStyle = 'lc-red';
          line2ChangeStyle = 'lc-green';
        } else if (gl.MoneyLine1 < newGl.MoneyLine1) {
          line1ChangeStyle = 'lc-green';
          line2ChangeStyle = 'lc-red';
        }


        break;
      case 'L':

        if (gl.TotalPoints > newGl.TotalPoints) {

          line1ChangeStyle = 'lc-green';
          line2ChangeStyle = 'lc-red';
        } else if (gl.TotalPoints < newGl.TotalPoints) {
          line1ChangeStyle = 'lc-red'; // O
          line2ChangeStyle = 'lc-green'; // U
        } else if (gl.TtlPtsAdj1 > newGl.TtlPtsAdj1) {
          // line1ChangeStyle = 'lc-green';
          // line2ChangeStyle = 'lc-red';
          line1ChangeStyle = 'lc-red';
          line2ChangeStyle = 'lc-green';
        } else if (gl.TtlPtsAdj1 < newGl.TtlPtsAdj1) {
          // line1ChangeStyle = 'lc-red'; // O
          // line2ChangeStyle = 'lc-green'; // U
          line1ChangeStyle = 'lc-green'; // O
          line2ChangeStyle = 'lc-red'; // U
        }

        break;
      case 'E':

        if (gl.Team1TotalPoints > newGl.Team1TotalPoints) {
          line1ChangeStyle = 'lc-green'; // O
          line2ChangeStyle = 'lc-red'; // U
        } else if (gl.Team1TotalPoints < newGl.Team1TotalPoints) {
          line1ChangeStyle = 'lc-red';
          line2ChangeStyle = 'lc-green';
        }


        if (gl.Team2TotalPoints > newGl.Team2TotalPoints) {
          line1ChangeStyle = 'lc-green'; // O
          line2ChangeStyle = 'lc-red'; // U
        } else if (gl.Team2TotalPoints < newGl.Team2TotalPoints) {
          line1ChangeStyle = 'lc-red';
          line2ChangeStyle = 'lc-green';
        }

        break;
    }

    return {
      line1ChangeStyle: line1ChangeStyle,
      line2ChangeStyle: line2ChangeStyle
    };
  }

  window.updateGameLineData = function (gl, newGl, wagerType, controlCode, isUpdate) {

    gl.Status = newGl.Status;
    if (newGl.CustProfile) gl.CustProfile = newGl.CustProfile.trim();

    gl.CircledMaxWagerSpreadType = newGl.CircledMaxWagerSpread > 0 ? newGl.CircledMaxWagerSpreadType : "";
    gl.CircledMaxWagerTotalType = newGl.CircledMaxWagerTotal > 0 ? newGl.CircledMaxWagerTotalType : "";
    gl.CircledMaxWagerMoneyLineType = newGl.CircledMaxWagerMoneyLine > 0 ? newGl.CircledMaxWagerMoneyLineType : "";
    gl.CircledMaxWagerTeamTotalType = newGl.CircledMaxWagerTeamTotal > 0 ? newGl.CircledMaxWagerTeamTotalType : "";

    gl.CircledMaxWagerSpread = newGl.CircledMaxWagerSpread;
    gl.CircledMaxWagerMoneyLine = newGl.CircledMaxWagerMoneyLine;
    gl.CircledMaxWagerTotal = newGl.CircledMaxWagerTotal;
    gl.CircledMaxWagerTeamTotal = newGl.CircledMaxWagerTeamTotal;


    //newGl.CircledInfoVisible = isCircledVisible(gl);

    if (!isUpdate || (
        (wagerType == "S" || wagerType == null)
        && (
          (
            Math.abs(gl.Spread1) != Math.abs(newGl.Spread1) ||
      Math.abs(gl.Spread2) != Math.abs(newGl.Spread2) ||
      gl.SpreadAdj1 != newGl.SpreadAdj1 ||
            gl.SpreadAdj2 != newGl.SpreadAdj2 ||
            gl.FavoredTeamID != newGl.FavoredTeamID
          )
        && gl.FavoredTeamID != null))) {

      newGl.WagerType = "S";
      gl.CircledMaxWagerSpread = newGl.CircledMaxWagerSpread;

      var lineChangeStyle = getLineChangeStyle('S', gl, newGl);
      gl.SpreadLine1ChangeStyle = lineChangeStyle.line1ChangeStyle;
      gl.SpreadLine2ChangeStyle = lineChangeStyle.line2ChangeStyle;

      if (!controlCode || controlCode == 'S1' || controlCode == 'S2') {
        gl.OrigSpreadAdj1 = gl.SpreadAdj1;
        gl.Spread1 = newGl.Spread1; //(gl.FavoredTeamID.trim() == gl.Team1ID.trim() ? newGl.Spread : newGl.Spread * -1);
        gl.SpreadAdj1 = newGl.SpreadAdj1;
        gl.SpreadDecimal1 = newGl.SpreadDecimal1;
        gl.SpreadNumerator1 = newGl.SpreadNumerator1;
        gl.SpreadDenominator1 = newGl.SpreadDenominator1;
        gl.OrigSpreadAdj2 = gl.SpreadAdj2;
        gl.Spread2 = newGl.Spread2; //(gl.FavoredTeamID.trim() == gl.Team2ID.trim() ? newGl.Spread : newGl.Spread * -1);
        gl.Spread = newGl.Spread;
        gl.SpreadAdj2 = newGl.SpreadAdj2;
        gl.SpreadDecimal2 = newGl.SpreadDecimal2;
        gl.SpreadNumerator2 = newGl.SpreadNumerator2;
        gl.SpreadDenominator2 = newGl.SpreadDenominator2;
      }
      if (gl.FavoredTeamID != newGl.FavoredTeamID) gl.FavoredTeamID = newGl.FavoredTeamID;

      gl.SpreadChanged = isUpdate;
      gl.MaxWagerSpreadType = newGl.MaxWagerSpreadType;
      gl.MaxWagerSpread = newGl.MaxWagerSpread;

      //Circled fields
      if (isUpdate) gl.MaxWagerSpread = (newGl.MaxWagerSpread < gl.MaxWagerSpread ? newGl.MaxWagerSpread : gl.MaxWagerSpread);
      else gl.MaxWagerSpread = newGl.MaxWagerSpread;
    }

    if (!isUpdate || ((wagerType == "M" || wagerType == null) && (gl.MoneyLine1 != newGl.MoneyLine1 || gl.MoneyLine2 != newGl.MoneyLine2 || gl.MoneyLineDraw != newGl.MoneyLineDraw))) {
      newGl.WagerType = "M";

      gl.CircledMaxWagerMoneyLine = newGl.CircledMaxWagerMoneyLine;

      var lineChangeStyle = getLineChangeStyle('M', gl, newGl);
      gl.MoneyLine1ChangeStyle = lineChangeStyle.line1ChangeStyle;
      gl.MoneyLine2ChangeStyle = lineChangeStyle.line2ChangeStyle;

      if (!controlCode || controlCode == 'M1' || controlCode == 'M2' || controlCode == 'M3') {
        gl.MoneyLine1 = newGl.MoneyLine1;
        gl.OrigMoneyLine1 = gl.MoneyLine1;
        gl.MoneyLineDecimal1 = newGl.MoneyLineDecimal1;
        gl.MoneyLineNumerator1 = newGl.MoneyLineNumerator1;
        gl.MoneyLineDenominator1 = newGl.MoneyLineDenominator1;

        gl.MoneyLine2 = newGl.MoneyLine2;
        gl.OrigMoneyLine2 = gl.MoneyLine2;
        gl.MoneyLineDecimal2 = newGl.MoneyLineDecimal2;
        gl.MoneyLineNumerator2 = newGl.MoneyLineNumerator2;
        gl.MoneyLineDenominator2 = newGl.MoneyLineDenominator2;
        gl.MoneyLineDraw = newGl.MoneyLineDraw;
        gl.MoneyLineDecimalDraw = newGl.MoneyLineDecimalDraw;
        gl.MoneyLineNumeratorDraw = newGl.MoneyLineNumeratorDraw;
        gl.MoneyLineDenominatorDraw = newGl.MoneyLineDenominatorDraw;
      }
      gl.MoneyLineChanged = isUpdate;
      gl.MaxWagerMoneyLineType = newGl.MaxWagerMoneyLineType;
      gl.MaxWagerMoneyLine = newGl.MaxWagerMoneyLine;

      //Circled fields
      if (isUpdate) gl.MaxWagerMoneyLine = (newGl.MaxWagerMoneyLine < gl.MaxWagerMoneyLine ? newGl.MaxWagerMoneyLine : gl.MaxWagerMoneyLine);
      else gl.MaxWagerMoneyLine = newGl.MaxWagerMoneyLine;
    }

    if (!isUpdate || ((wagerType == "L" || wagerType == null) && (gl.TotalPoints1 != newGl.TotalPoints1 || gl.TotalPoints2 != newGl.TotalPoints2 ||
      gl.TotalPoints != newGl.TotalPoints || gl.TtlPtsAdj1 != newGl.TtlPtsAdj1 || gl.TtlPtsAdj2 != newGl.TtlPtsAdj2))) {
      newGl.WagerType = "L";

      var lineChangeStyle = getLineChangeStyle('L', gl, newGl);
      gl.TotalPoints1ChangeStyle = lineChangeStyle.line1ChangeStyle;
      gl.TotalPoints2ChangeStyle = lineChangeStyle.line2ChangeStyle;


      if (!controlCode || controlCode == 'L1' || controlCode == 'L2') {
        gl.TotalPoints1 = newGl.TotalPoints1;
        gl.OrigTtlPtsAdj1 = gl.TtlPtsAdj1;
        gl.TtlPtsAdj1 = newGl.TtlPtsAdj1;
        gl.TtlPointsDecimal1 = newGl.TtlPointsDecimal1;
        gl.TtlPointsNumerator1 = newGl.TtlPointsNumerator1;
        gl.TtlPointsDenominator1 = newGl.TtlPointsDenominator1;
        gl.TotalPoints2 = newGl.TotalPoints2;
        gl.OrigTtlPtsAdj2 = gl.TtlPtsAdj2;
        gl.TtlPtsAdj2 = newGl.TtlPtsAdj2;
        gl.TtlPointsDecimal2 = newGl.TtlPointsDecimal2;
        gl.TtlPointsNumerator2 = newGl.TtlPointsNumerator2;
        gl.TtlPointsDenominator2 = newGl.TtlPointsDenominator2;
      }

      gl.TotalPoints = newGl.TotalPoints;
      gl.TotalPointsChanged = isUpdate;
      gl.MaxWagerTotalType = newGl.MaxWagerTotalType;
      gl.MaxWagerTotal = newGl.MaxWagerTotal;

      //Circled fields
      if (isUpdate) gl.MaxWagerTotal = (newGl.MaxWagerTotal < gl.MaxWagerTotal ? newGl.MaxWagerTotal : gl.MaxWagerTotal);
      else gl.MaxWagerTotal = newGl.MaxWagerTotal;
    }

    if (newGl.PeriodNumber == 0 && (!isUpdate || ((wagerType == "E" || wagerType == null) && (gl.Team1TotalPoints != newGl.Team1TotalPoints || gl.Team1TtlPtsAdj1 != newGl.Team1TtlPtsAdj1 ||
      gl.Team1TtlPtsAdj2 != newGl.Team1TtlPtsAdj2)))) {
      newGl.WagerType = "E";

      gl.CircledMaxWagerTeamTotal = newGl.CircledMaxWagerTeamTotal;
      gl.Team1TotalPoints = newGl.Team1TotalPoints;

      var lineChangeStyle = getLineChangeStyle('E', gl, newGl);
      gl.TeamTotal1Team1ChangeStyle = lineChangeStyle.line1ChangeStyle;
      gl.TeamTotal2Team1ChangeStyle = lineChangeStyle.line2ChangeStyle;

      if (!controlCode || controlCode == 'E1' || controlCode == 'E4') {
        gl.OrigTeam1TtlPtsAdj1 = gl.Team1TtlPtsAdj1;
        gl.Team1TtlPtsAdj1 = newGl.Team1TtlPtsAdj1;
        gl.Team1TtlPtsDecimal1 = newGl.Team1TtlPtsDecimal1;
        gl.Team1TtlPtsNumerator1 = newGl.Team1TtlPtsNumerator1;
        gl.Team1TtlPtsDenominator1 = newGl.Team1TtlPtsDenominator1;
        gl.OrigTeam1TtlPtsAdj2 = gl.Team1TtlPtsAdj2;
        gl.Team1TtlPtsAdj2 = newGl.Team1TtlPtsAdj2;
        gl.Team1TtlPtsDecimal2 = newGl.Team1TtlPtsDecimal2;
        gl.Team1TtlPtsNumerator2 = newGl.Team1TtlPtsNumerator2;
        gl.Team1TtlPtsDenominator2 = newGl.Team1TtlPtsDenominator2;
      }

      gl.TeamTotalChanged = isUpdate;
      gl.MaxWagerTeamTotal = newGl.MaxWagerTeamTotal;
      //Circled fields
      if (isUpdate) gl.MaxWagerTeamTotal = (newGl.MaxWagerTeamTotal < gl.MaxWagerTeamTotal ? newGl.MaxWagerTeamTotal : gl.MaxWagerTeamTotal);
      else gl.MaxWagerTeamTotal = newGl.MaxWagerTeamTotal;
    }
    if (!isUpdate || gl.Team2TotalPoints != newGl.Team2TotalPoints || gl.Team2TtlPtsAdj1 != newGl.Team2TtlPtsAdj1 || gl.Team2TtlPtsAdj2 != newGl.Team2TtlPtsAdj2) {
      newGl.WagerType = "E";

      gl.CircledMaxWagerTeamTotal = newGl.CircledMaxWagerTeamTotal;
      gl.Team2TotalPoints = newGl.Team2TotalPoints;

      var lineChangeStyle = getLineChangeStyle('E', gl, newGl);
      gl.TeamTotal1Team2ChangeStyle = lineChangeStyle.line1ChangeStyle;
      gl.TeamTotal2Team2ChangeStyle = lineChangeStyle.line2ChangeStyle;

      if (!controlCode || controlCode == 'E2' || controlCode == 'E3') {
        gl.OrigTeam2TtlPtsAdj1 = newGl.Team2TtlPtsAdj1;
        gl.Team2TtlPtsAdj1 = newGl.Team2TtlPtsAdj1;
        gl.Team2TtlPtsDecimal1 = newGl.Team2TtlPtsDecimal1;
        gl.Team2TtlPtsNumerator1 = newGl.Team2TtlPtsNumerator1;
        gl.Team2TtlPtsDenominator1 = newGl.Team2TtlPtsDenominator1;
        gl.OrigTeam2TtlPtsAdj2 = newGl.Team2TtlPtsAdj2;
        gl.Team2TtlPtsAdj2 = newGl.Team2TtlPtsAdj2;
        gl.Team2TtlPtsDecimal2 = newGl.Team2TtlPtsDecimal2;
        gl.Team2TtlPtsNumerator2 = newGl.Team2TtlPtsNumerator2;
        gl.Team2TtlPtsDenominator2 = newGl.Team2TtlPtsDenominator2;
      }
      gl.TeamTotalChanged = isUpdate;
      gl.MaxWagerTeamTotal = newGl.MaxWagerTeamTotal;
      //Circled fields
      if (isUpdate) gl.MaxWagerTeamTotal = (newGl.MaxWagerTeamTotal < gl.MaxWagerTeamTotal ? newGl.MaxWagerTeamTotal : gl.MaxWagerTeamTotal);
      else gl.MaxWagerTeamTotal = newGl.MaxWagerTeamTotal;
    }

    if (gl.SpreadChanged || gl.MoneyLineChanged || gl.TotalPointsChanged || gl.TeamTotalChanged) {
      var _RestoreChangedLine = function (game) {
        setTimeout(function () {
          if (game.SpreadChanged) game.SpreadChanged = false;
          if (game.MoneyLineChanged) game.MoneyLineChanged = false;
          if (game.TeamTotalChanged) game.TeamTotalChanged = false;
          if (game.TotalPointsChanged) game.TotalPointsChanged = false;
          $(".line_state").removeClass("line_up line_up_green line_up_red line_down line_down_green line_down_red");
          $rootScope.safeApply();
        }, 30000);
      };
      _RestoreChangedLine(gl);
    }

    syncLineCircles(gl);

  };

  function removeEmptyLines() {
    for (var a = 0; a < _sportsAndContestsService.Selections.length; a++) {
      var selection = _sportsAndContestsService.Selections[a];
      if (typeof selection.Lines == "undefined") continue;
      for (var j = selection.Lines.length - 1; j >= 0; j--) {
        var l = selection.Lines[j];
        if (l.Status == 'H' || (l.Spread1 == null && l.Spread2 == null && l.MoneyLine1 == null && l.MoneyLine2 == null && l.TotalPoints == null && !l.IsTitle)) {
          selection.Lines.splice(j, 1);

          if(!$ticketService.Ticket.Posted()){
            for (var k = 0; k < $ticketService.Ticket.WagerItems.length; k++) {
              var wi = $ticketService.Ticket.WagerItems[k];
              if (wi.Type == "G") {
                if (wi.Loo.GameNum == l.GameNum &&
                  wi.Loo.PeriodNumber == l.PeriodNumber &&
                  wi.Loo.Store == l.Store) {


                    $ticketService.Ticket.WagerItems.splice(k, 1);

                    if ($wagerTypesService.IsAccumWager()) {
                      $ticketService.ResetAmounts();
                      if ($wagerTypesService.IsParlay()) $ticketService.GetParlayInfo(null);
                      else if ($wagerTypesService.IsTeaser() && $ticketService.Ticket.TeaserName) $ticketService.GetTeaserInfo();
                    }


                  break;
                }
              }
            }
          }

          $ticketService.CalculateTotalAmounts();
          return true;
        }
      };
    };
    return false;
  };

  function gameLineUpdate(lChanged, selection) {
    if ($wagerTypesService.IsTeaser() && lChanged.PeriodNumber > 0) {
      return false;
    }
    var wt = $wagerTypesService.Selected;
    for (var i = 0; i < selection.Lines.length; i++) {
      var line = selection.Lines[i];
      if (line.GameNum == lChanged.GameNum && line.PeriodNumber == lChanged.PeriodNumber) {
        if (!isIfBetWagerItem(line.GameNum, line.PeriodNumber, wt)) {
          //if (line.PeriodNumber == lChanged.PeriodNumber) {
          _caller.POST({ 'newItem': lChanged, 'eventOffering': 'G', 'wagerType': wt.name }, 'ProcessLineChange', null, true).then(function (result) {
            var nLoo = result != null && result.NLoo != null ? result.NLoo : null;
            if (nLoo) window.updateGameLineData(line, nLoo, null, null, true);
            else line.Status = 'H';
            var wagerItems = result != null && result.wagerItems != null ? result.wagerItems : null;
            if (wagerItems) {
              wagerItems.forEach(function (wager) {
                if (!wager.IsOk && wager.Changed) wager.IsOk = true;
                if (wager.Changed || !wager.IsOk) {
                  $ticketService.Ticket.RRTotalRiskAmount = 0;
                  $ticketService.Ticket.TotalRiskAmount = 0;
                  $ticketService.Ticket.TotalToWinAmount = 0;
                  $ticketService.Ticket.ArAmount = 0;
                  wager.RiskAmt = 0;
                  wager.ToWinAmt = 0;
                  $ticketService.Ticket.ArAmount = null;
                }
                $ticketService.WagerAvailable(wager, $ticketService.UpdateGameWager(wager, $customerService.AutoAccept, true));
              });
            }
            syncLineCircles(line);
            removeEmptyLines();
            $rootScope.safeApply();
          });
          //}
          return;
        }
      }
    }

    //If line is not found then it is added.
    _caller.POST({ 'newItem': lChanged, 'eventOffering': 'G', 'wagerType': wt.name }, 'ProcessLineChange', null, true).then(function (result) {
      var nLoo = result != null && result.NLoo != null ? result.NLoo : null;
      if (nLoo != null) {
        nLoo.ShowDate = false;
        nLoo.ScheduleDateF = CommonFunctions.FormatDateTime(nLoo.ScheduleDateString, 1);
        syncLine(selection.Lines, nLoo);
        addPeriod(selection.Periods, nLoo.PeriodNumber, nLoo.PeriodDescription);
        $rootScope.safeApply();
      }
    });

  }

  function syncLine(linesArray, newLine) {
    for (var i = 0; i < linesArray.length; i++) {
      var oldLine = linesArray[i];
      if (newLine.GameNum == oldLine.GameNum && newLine.PeriodNumber == oldLine.PeriodNumber) {
        window.updateGameLineData(oldLine, newLine, null, null, false);
        return;
      }
    }
    linesArray.push(newLine);
  }

  function addPeriod(periods, periodNumber, periodDescription) {
    for (var i = 0; i < periods.length; i++) {
      if (periods[i].PeriodNumber == periodNumber) return;
    }
    periods.push({ PeriodNumber: periodNumber, PeriodDescription: periodDescription });
  }

  function groupSportsAndContests(rawSportsData) {
    if (!rawSportsData)
      return null;

    var groupedData = new Array();
    var currentSport = null;
    var holdSportType = null;
    var holdSportSubType = null;
    //var holdContestType = null;
    var selectable = false;
    var inactiveSportsOrder = 0;
    var isInactiveSport = false;
    var holdOfferingType = null;

    for (var i = 0; i < rawSportsData.length; i++) {
      var el = rawSportsData[i];
      if (el.NextEventDateTimeStr) el.NextEventDateTime = moment(el.NextEventDateTimeStr);
      if (holdSportType != el.SportType) {
        isInactiveSport = $.inArray(el.SportType, SETTINGS.ShowInactiveSports) >= 0;
        if (!el.Active && !isInactiveSport) continue;
        if (isInactiveSport) inactiveSportsOrder++;
        if (holdSportType != null && currentSport != null) groupedData.push(currentSport);
        currentSport = { "SportType": el.SportType, "ContestType": el.ContestType, "SequenceNumber": isInactiveSport ? inactiveSportsOrder : el.SequenceNumber, "SportSubTypes": new Array() };
        holdSportSubType = null;
      }
      if (!el.Active && !isInactiveSport) continue;
      if (el.SportSubType != null && el.SportSubType != '') {
        selectable = true;
                if (holdSportSubType != el.SportSubType || holdOfferingType != el.OfferingType) currentSport.SportSubTypes.push({ "SportType": el.SportType, "SportSubType": el.SportSubType, "SequenceNumber": el.SequenceNumber, "ContestType": el.ContestType, "ContestType2": el.ContestType2, "Selected": false, "Selectable": selectable, "Type": el.OfferingType, "Active": el.Active, "NextEventDateTime": el.NextEventDateTime, "FirstRotNum": el.FirstRotNum, "SportSubTypeDisplayName": (el.SportSubTypeDisplayName || "").trim() });
      }
      holdSportType = el.SportType;
      holdSportSubType = el.SportSubType;
      holdOfferingType = el.OfferingType;
    }
    if (currentSport != null)
      groupedData.push(currentSport);
    return groupedData;
  };

  function groupTeaserSports(teaserSports) {
    if (!teaserSports) return [];
    var groupedData = new Array();
    var holdSport;

    for (var i = 0; i < teaserSports.length; i++) {
      var sport = teaserSports[i];
      sport.GameLines.forEach(function (line) {
        line.ActivePeriod = sport.Periods[0];
        line.SportLimits = sport.SportLimits;
      });
      var offering = { "AddingSport": false, "GroupValue": "", "IncludeTeamTotals": false, "Lines": sport.GameLines, "OrderIndex": 0, "Periods": sport.Periods, "ActivePeriod": sport.Periods[0], "SportSubType": sport.SportSubType, "SportType": sport.SportType, "Type": "G", "SportLimits": sport.SportLimits };
      var leagueData = { "SportSubType": sport.SportSubType, "SequenceNumber": i, "Selected": false, "Selectable": false, "Type": "G", "Offering": offering };
      if (holdSport != sport.SportType) {
        var sportData = { "SportType": sport.SportType, "SequenceNumber": i, "SportSubTypes": [leagueData] };
        groupedData.push(sportData);
        continue;
      }
      groupedData[groupedData.length - 1].SportSubTypes.push(leagueData);
    }
    return groupedData;
  };

  function bindTicketContestWagers(contestantLine) {
    contestantLine.Selected = false;
    for (var i = 0; i < $ticketService.Ticket.WagerItems.length; i++) {
      var wagerItem = $ticketService.Ticket.WagerItems[i];
      if (contestantLine.ContestNum == wagerItem.Loo.ContestNum && contestantLine.ContestantNum == wagerItem.Loo.ContestantNum) {
        contestantLine.Selected = true;
        wagerItem.Loo = contestantLine;
        break;
      }
    }
  };

    function getAlternateLinesGroupByParent(lines){
        let childLinesParentGameNum = lines.filter(line => line.ParentGameNum != null);
        const groupByCategory = childLinesParentGameNum.reduce((group, line) => {
            const { ParentGameNum } = line;
            //group[ParentGameNum] = group[ParentGameNum] ?? [];
            if(!group[ParentGameNum])
                group[ParentGameNum] = [];

            group[ParentGameNum].push(line);
            return group;
        }, {});

        return groupByCategory;
    }

  function bindGameLines(subSport) {
    if (!subSport || !subSport.Offering) {
      $rootScope.LinesLoading = false;
      return;
    }
    for (var i = 0; i < _sportsAndContestsService.Selections.length; i++) {
      if (_sportsAndContestsService.Selections[i].Lines) {
        for (var j = 0; j < _sportsAndContestsService.Selections[i].Lines.length; j++) {
          for (var k = 0; k < subSport.Offering.Lines.length; k++) {
            if (_sportsAndContestsService.Selections[i].Lines[j].GameNum == subSport.Offering.Lines[k].GameNum) subSport.Offering.Lines.splice(k, 1);
          }
        }
      }
    }
    var previusDate = "";
    for (var l = 0; l < subSport.Offering.Lines.length; l++) {
      var gameLine = subSport.Offering.Lines[l];
      gameLine.ScheduleDateF = CommonFunctions.FormatDateTime(gameLine.ScheduleDateString, 1);
      gameLine.ShowDate = false;
      gameLine.Available = true;
      var toDate = new Date(gameLine.GameDateTimeString);
      var actualDate = toDate.getDate().toString() + "" + toDate.getMonth().toString();
      if (l == 0) {
        previusDate = actualDate;
        gameLine.ShowDate = true;
      }
      if (previusDate != actualDate) {
        previusDate = actualDate;
        gameLine.ShowDate = true;
      }
      gameLine.GameDate = new Date(gameLine.GameDate);
    }
    //Esta linea hace que solo se pueda seleccionar uno a la vez, remover para volver a funcionalidad anterior
      if ($rootScope.UISettings && !$rootScope.UISettings.MultiSelectSportSubtype) {
        _sportsAndContestsService.Selections.splice(0);
      }

    if (subSport.Offering.Lines.length > 0) {
      _sportsAndContestsService.Selections.push(subSport.Offering);
      fixSelectionOnSubSport();
    }
    subSport.SelectionIndex = _sportsAndContestsService.Selections.length - 1;
    $rootScope.LinesLoading = false;
  };

  function unbindGameLines(sport, subSport) {
    for (var i = _sportsAndContestsService.Selections.length - 1; i >= 0; i--) {
      if (_sportsAndContestsService.Selections[i].Type == 'G' && subSport && subSport.Offering && _sportsAndContestsService.Selections[i].SportSubType == subSport.Offering.SportSubType)
        _sportsAndContestsService.Selections.splice(i, 1);
    }
  };

  function bindContestLines(contests, isSpotlight) {

    isSpotlight = typeof isSpotlight != 'undefined' ? isSpotlight : false;
    if ($rootScope.UISettings && !$rootScope.UISettings.MultiSelectSportSubtype) {
      _sportsAndContestsService.Selections.splice(0);
    }
    for (var i = 0; i < contests.Offering.length; i++) {
      var holdContestNum = 0;
      var holdContestantNum = 0;
      var toDelete = new Array();
      for (var j = 0; j < contests.Offering[i].ContestantsLines.length; j++) {
        if (holdContestNum == contests.Offering[i].ContestNum && holdContestantNum == contests.Offering[i].ContestantsLines[j].ContestantNum)
          toDelete.push(j);
        else
          bindTicketContestWagers(contests.Offering[i].ContestantsLines[j]);
        holdContestNum = contests.Offering[i].ContestNum;
        holdContestantNum = contests.Offering[i].ContestantsLines[j].ContestantNum;
      }
      CommonFunctions.DeleteFromArray(contests.Offering[i].ContestantsLines, toDelete);
      contests.Offering[i].IsSpotlight = isSpotlight;
      _sportsAndContestsService.Selections.push(contests.Offering[i]);
    }
  };

  function unbindContestLines(contest) {
    for (var i = _sportsAndContestsService.Selections.length - 1; i >= 0; i--)
      if (_sportsAndContestsService.Selections[i].Type == 'C' && _sportsAndContestsService.Selections[i].ContestType == contest.ContestType && _sportsAndContestsService.Selections[i].ContestType2 == contest.ContestType2) {

        _sportsAndContestsService.Selections.splice(i, 1);

      }
    contest.Offering = null;
  };

  //Private Game Lines Methods

  function formatGameLines(linesOffering) {
    var periods = new Array();
    var glToDelete = new Array();
    var holdGameNum = 0;
    var holdPeriodNumber = -1;
    var ttFlag = false;
    var wtId = $wagerTypesService.Selected.id;
    for (var i = 0; i < linesOffering.length; i++) {
      var gameNum = linesOffering[i].GameNum;
      var periodNumber = linesOffering[i].PeriodNumber;
      if (linesOffering[i].PeriodDescription != null) addPeriod(periods, periodNumber, linesOffering[i].PeriodDescription.trim());
      if (gameNum == holdGameNum && holdPeriodNumber == periodNumber) glToDelete.push(i);
      holdGameNum = gameNum;
      holdPeriodNumber = periodNumber;

      linesOffering[i].Spread1Selected = false;
      linesOffering[i].Spread2Selected = false;
      linesOffering[i].MoneyLine1Selected = false;
      linesOffering[i].MoneyLine2Selected = false;
      linesOffering[i].MoneyLine3Selected = false;
      linesOffering[i].TotalPoints1Selected = false;
      linesOffering[i].TotalPoints2Selected = false;
      linesOffering[i].Team1TtlPtsAdj1Selected = false;
      linesOffering[i].Team1TtlPtsAdj2Selected = false;
      linesOffering[i].Team2TtlPtsAdj1Selected = false;
      linesOffering[i].Team2TtlPtsAdj2Selected = false;
      if (wtId == $wagerTypesService.Ids.StraightBet && !ttFlag && ((linesOffering[i].Team1TtlPtsAdj1 != null && linesOffering[i].Team1TtlPtsAdj2 != null) || (linesOffering[i].Team2TtlPtsAdj1 && linesOffering[i].Team2TtlPtsAdj2))) { //Only Straight bets are allowed for team totals
        ttFlag = true;
      }
    }
    periods.sort(CommonFunctions.DynamicSort("PeriodNumber"));
    CommonFunctions.DeleteFromArray(linesOffering, glToDelete);
    return { 'Periods': periods, 'IncludeTeamTotals': ttFlag };
  };

  function syncLineCircles(line) {
    if (!line) return;
    var subSportLimit = null;
    if (line.SportLimits) {
      for (var i = 0; i < line.SportLimits.length; i++) {
        if (line.PeriodNumber == line.SportLimits[i].PeriodNumber) {
          subSportLimit = line.SportLimits[i];
          break;
        }
      }
    }
    if (subSportLimit) {
      line.CircledMaxWagerSpreadType = (!line.CircledMaxWagerSpread || line.Status != "I" ? '' : (subSportLimit.MaxWagerSpread > line.CircledMaxWagerSpread ? line.CircledMaxWagerSpreadType : subSportLimit.MaxWagerSpreadType));
      line.CircledMaxWagerTotalType = (!line.CircledMaxWagerTotal || line.Status != "I" ? '' : (subSportLimit.MaxWagerTotal > line.CircledMaxWagerTotal ? line.CircledMaxWagerTotalType : subSportLimit.MaxWagerTotalType));
      line.CircledMaxWagerMoneyLineType = (!line.CircledMaxWagerMoneyLine || line.Status != "I" ? '' : ((subSportLimit.MaxWagerMoneyLine || 0) > line.CircledMaxWagerMoneyLine ? line.CircledMaxWagerMoneyLineType : subSportLimit.MaxWagerMoneyLineType));
      line.CircledMaxWagerTeamTotalType = (!line.CircledMaxWagerTeamTotal || line.Status != "I" ? '' : (subSportLimit.MaxWagerTeamTotal > line.CircledMaxWagerTeamTotal ? line.CircledMaxWagerTeamTotalType : subSportLimit.MaxWagerTeamTotalType));

      line.CircledMaxWagerSpread = (!line.CircledMaxWagerSpread || line.Status != "I" ? null : (subSportLimit.MaxWagerSpread > line.CircledMaxWagerSpread ? line.CircledMaxWagerSpread : subSportLimit.MaxWagerSpread));
      line.CircledMaxWagerTotal = (!line.CircledMaxWagerTotal || line.Status != "I" ? null : (subSportLimit.MaxWagerTotal > line.CircledMaxWagerTotal ? line.CircledMaxWagerTotal : subSportLimit.MaxWagerTotal));
      line.CircledMaxWagerMoneyLine = (!line.CircledMaxWagerMoneyLine || line.Status != "I" ? null : ((subSportLimit.MaxWagerMoneyLine || 0) > line.CircledMaxWagerMoneyLine ? line.CircledMaxWagerMoneyLine : subSportLimit.MaxWagerMoneyLine));
      line.CircledMaxWagerTeamTotal = (!line.CircledMaxWagerTeamTotal || line.Status != "I" ? null : (subSportLimit.MaxWagerTeamTotal > line.CircledMaxWagerTeamTotal ? line.CircledMaxWagerTeamTotal : subSportLimit.MaxWagerTeamTotal));
    }
    line.CircledInfoVisible = isCircledVisible(line);

  }

  function syncSportLineCircles(subSport) {
    for (var i = 0; i < subSport.Offering.Lines.length; i++) {
      var line = subSport.Offering.Lines[i];
      line.ActivePeriod = subSport.Offering.ActivePeriod;
      line.SportLimits = subSport.Offering.SportLimits[line.PeriodNumber];
      syncLineCircles(line);
    }
  }

     function capitalizeFirstLetter(val) {
    return String(val).charAt(0).toUpperCase() + String(val).slice(1);
  }

  // function groupCustomPropsBySchedule(lines){
  //   const groupByCategory = lines.reduce((group, line) => {
  //     const { ScheduleText } = line;
  //     //group[ParentGameNum] = group[ParentGameNum] ?? [];
  //     var normalizedText = ScheduleText.toLowerCase();
  //     normalizedText = capitalizeFirstLetter(normalizedText);
  //
  //     if(!group[normalizedText])
  //       group[normalizedText] = [];
  //
  //     group[normalizedText].push(line);
  //     return group;
  //   }, {});
  //
  //   return groupByCategory;
  // }

  function groupCustomPropsBySchedule(lines) {
    const groupByCategory = lines.reduce((group, line) => {
      let { ScheduleText } = line;

      // fallback if ScheduleText doesn't exist or is empty
      if (!ScheduleText) {
        ScheduleText = "Player Props";
      }

      let normalizedText = ScheduleText.toLowerCase();
      normalizedText = capitalizeFirstLetter(normalizedText);

      if (!group[normalizedText]) {
        group[normalizedText] = [];
      }

      group[normalizedText].push(line);
      return group;
    }, {});

    return groupByCategory;
  }

  async function test(){
    
  }

  function loadCustomProps(sport, periodNumber, gameNum = null, requestMode = 'P') {
    var wagerType = $wagerTypesService.Selected;
    var teaserName = $wagerTypesService.IsTeaser() && $ticketService.Ticket.TeaserName ? $ticketService.Ticket.TeaserName : "";
    return _caller.POST(
        {
          'sportType': sport, 'sportSubType': null, 'wagerType': wagerType.name,
          'hoursAdjustment': 0, 'periodNumber': periodNumber, 'gameNum': gameNum, 'parentGameNum': null, 'teaserName': teaserName,
          'requestMode': requestMode
        }, 'GetSportOffering').then(function (response) {
          if (!response || response == "" || response.length == 0 || !response.GameLines || !response.GameLines.length) return false;
          var params = formatGameLines(response.GameLines);
          var groupedLines = groupCustomPropsBySchedule(response.GameLines);
          return groupedLines;
        }

    )
  }

  function loadSportLines(sport, subSport, periodNumber, gameNum = null) {
    var wagerType = $wagerTypesService.Selected;
    var teaserName = $wagerTypesService.IsTeaser() && $ticketService.Ticket.TeaserName ? $ticketService.Ticket.TeaserName : "";
    if (subSport && subSport.Offering) subSport.Offering.Lines = [];
    return _caller.POST(
      {
        'sportType': sport.SportType, 'sportSubType': subSport.SportSubType, 'wagerType': wagerType.name,
        'hoursAdjustment': 0, 'periodNumber': periodNumber, 'gameNum': gameNum, 'parentGameNum': null, 'teaserName': teaserName,
        'requestMode':null
      }, 'GetSportOffering').then(function (response) {
    if (!response || response == "" || response.length == 0 || !response.GameLines || !response.GameLines.length) return false;
    var params = formatGameLines(response.GameLines);
                    //----------------------------------
                    //mark parentAlternateGameNum
                    //----------------------------------
			let gameLines = response.GameLines;
			let _alternateLines = getAlternateLinesGroupByParent(gameLines);
			let tmpAlternates = [];
			
			var _alternates =  gameLines.filter(line => line.ParentGameNum != null);
			var allAreAlternates = gameLines.length == _alternates.length;
			
			
			let offeringWithAlternates = [];
			if(Object.keys(_alternateLines).length > 0 && !allAreAlternates){
				offeringWithAlternates = gameLines.filter(line => line.ParentGameNum == null).map(
					gameLine =>  {
                                let initCount = 0;
						if(_alternateLines[gameLine.GameNum]){
							tmpAlternates = _alternateLines[gameLine.GameNum].filter(al=>al.PeriodNumber == gameLine.PeriodNumber);
							if(tmpAlternates.length){
								gameLine.AlternateLines =  tmpAlternates;
                                        gameLine.AlternateCounter = tmpAlternates.reduce(
                                          (accumulator, gameLineValue) =>
                                              accumulator
                                              + (!!gameLineValue.Spread1) * 1
                                              + (!!gameLineValue.MoneyLine1) * 1
                                              + (!!gameLineValue.TotalPoints1) * 1
                                              + (!!gameLineValue.Team1TotalPoints) * 1,
                                          initCount
                               );
								gameLine.hasAlternates = true;
							}
						return gameLine;
					   }else{
						return gameLine;
					   }


					}
				);
				gameLines = offeringWithAlternates;
			}

              /*
              FIX ORPHAN CHILDS
              ---------------------------------------------------------------

              //offeringWithAlternates have all Fathers with respectives childs
              //but childs with no fathers are missing

              //if all are alternates not reach this code

              */
              if (offeringWithAlternates && offeringWithAlternates.length){
                var parents = [];

                var orphanChilds = gameLines.filter(line => line.ParentGameNum != null);

                //remove alternates with fathher belongs other league (orphan chils)
                orphanChilds = orphanChilds.filter(ww =>
                {
                  parents = offeringWithAlternates.filter(line => line.GameNum == ww.ParentGameNum );
                  return !parents.length;
                });

                gameLines = [...offeringWithAlternates, ...orphanChilds];
              }

                    //----------------------------------
                    //end : mark parentAlternateGameNum
                    //----------------------------------

                gameLines = gameLines.map(function(gameLine){
                  //more lines counter
                  // gameLine.LinesTypeCounter =  !!gameLine.MoneyLine1 * 1;
                  gameLine.LinesTypeCounter = !!gameLine.SpreadDecimal1 * 1;
                  gameLine.LinesTypeCounter += !!gameLine.TotalPoints * 1;
                  gameLine.LinesTypeCounter += !!gameLine.Team1TotalPoints * 1;
                  gameLine.MoreMarketsLinesCounter = gameLine.LinesTypeCounter + (typeof gameLine.AlternateCounter == "undefined" ? 0 : gameLine.AlternateCounter);
                  return gameLine;
                });

                if (periodNumber == null) {
					subSport.Offering = {
					Type: "G",
					GroupValue: "",
					IncludeTeamTotals: params.IncludeTeamTotals,
					Periods: params.Periods,
					ActivePeriod: params.Periods[0],
					Lines: gameLines,
					OrderIndex: 0,
					PeriodDesc: "",
					SportSubTypeId: gameLines[0].SportSubTypeId,
					SportType: sport.SportType,
					SportSubType: subSport.SportSubType,
					TeamTotalLines: null,
					TeamTotalSelected: false,
					WagerType: wagerType,
					AddingSport: false,
					SportLimits: response.SportLimits,
					ScheduleDateString: gameLines[0].ScheduleDateString,
					FirstRotNum: gameLines[0].Team1RotNum
					};
      syncSportLineCircles(subSport);
    } else {
      addPeriod(sport.Periods, params.Periods[0].PeriodNumber, params.Periods[0].PeriodDescription);
      response.GameLines.forEach(function (l) {
        syncLine(sport.Lines, l);
      });
    }
    $rootScope.safeApply();
      });
  };

  /*
  function loadSpotlightSportLines() {
    var wagerType = $wagerTypesService.Selected;
    return _caller.POST({ 'wagerType': wagerType.name, 'hoursAdjustment': 0, 'gameNum': null }, 'LoadSpotLightGameLines');
  }*/

  function groupSportLines(response) {
    var params = formatGameLines(response);
    var wagerType = $wagerTypesService.Selected;
    response[0].CircledInfoVisible = isCircledVisible(response[0], response[0]);
    return {
      Type: "G",
      GroupValue: "",
      IncludeTeamTotals: params.IncludeTeamTotals,
      Periods: params.Periods,
      ActivePeriod: params.Periods[0],
      Lines: response,
      OrderIndex: 0,
      PeriodDesc: "",
      SportSubTypeId: response[0].SportSubTypeId,
      SportType: response[0].SportType,
      SportSubType: response[0].SportSubType,
      TeamTotalLines: null,
      TeamTotalSelected: false,
      WagerType: wagerType,
      AddingSport: false,
      MaxWagerSpreadType: response[0].MaxWagerSpreadType,
      MaxWagerTotalType: response[0].MaxWagerTotalType,
      MaxWagerMoneyLineType: response[0].MaxWagerMoneyLineType,
      MaxWagerTeamTotalType: response[0].MaxWagerTeamTotalType
    };

  }

  //Private Contest Lines Methods

  function groupContests(contestList) {
    var contests = [];
    var contestType, contestType2, contestType3, contestDesc;
    for (var i = 0; i < contestList.length; i++) {
      if (contestType != contestList[i].ContestType ||
        contestType2 != contestList[i].ContestType2 ||
        contestType3 != contestList[i].ContestType3 ||
        contestDesc != contestList[i].ContestDesc) {
        contests.push(contestList[i]);
        contestList[i].Type = 'C';
      } else contests[contests.length - 1].ContestantsLines = contests[contests.length - 1].ContestantsLines.concat(contestList[i].ContestantsLines);

      contestType = contestList[i].ContestType;
      contestType2 = contestList[i].ContestType2;
      contestType3 = contestList[i].ContestType3;
      contestDesc = contestList[i].ContestDesc;
    }
    return contests;
  }

  function loadContestLines(contest) {
    return _caller.POST({ 'contestType': contest.ContestType, 'contestType2': contest.ContestType2 ? contest.ContestType2 : ".", 'contestType3': (typeof contest.ContestType3 == "undefined" ? null : contest.ContestType3) }, 'GetContestOffering').then(function (result) {
      var response = result;
      if (response == null || response == "" || response.length == 0) return false;
      response[0].SportType = contest.SportType;
      contest.Offering = groupContests(response);
      return true;
    });
  };

  function loadContestLinesByCorrelation(gameLine) {
    return _caller.POST({ 'correlation': gameLine.CorrelationID, 'correlatedGameNum': gameLine.GameNum }, 'GetCorrelatedContestOffering').then(function (result) {
      var response = result;
      if (!response) return false;
      var found = false;
      _sportsAndContestsService.Selections.forEach(function (s) {
        if (found) return;
        response.forEach(function (r) {
          if (s.ContestType2 == r.ContestType2) {
            found = true;
            return;
          }
        });
      });
      if (found) {
        UI.Notify($translatorService.Translate('Contest already open'),
          UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
        gameLine.Correlation = null;
        return false;
      }
      if (response.length == 0) return false;
      response[0].SportType = gameLine.SportType;
      gameLine.Correlation = groupContests(response);
      return true;
    });
  }

  /*
  function loadSpotlightContests() {
    return _caller.POST({ 'contestNum': null }, 'LoadSpotlightContests');
  }
  */

  function isSportSelected(sportType, sportSubType) {
    for (var i = 0; i < _sportsAndContestsService.Selections.length; i++) {
      var selection = _sportsAndContestsService.Selections[i];
      if (selection.SportType == sportType && selection.SportSubType == sportSubType)
        return true;
    }
    return false;
  };

  function subSportInSelection(subSport) {
    return _sportsAndContestsService.Selections.some(function (sel) { return subSport.SportSubTypeId == sel.SportSubTypeId; });
  };

  //Public Methods

  window.UpdateLineOffering = function (newLoo, wagerItem, isFromSocket) {
    var found = false;
    for (var i = 0; i < _sportsAndContestsService.SportsAndContests.length; i++) {
      var sport = _sportsAndContestsService.SportsAndContests[i];
      if (sport.SportType.trim() == newLoo.SportType) {
        for (var j = 0; j < sport.SportSubTypes.length; j++) {
          var subSport = sport.SportSubTypes[j];
          if (subSport.SportSubType.trim() == newLoo.SportSubType && subSport.Offering && subSport.Offering.Lines) {
            for (var k = 0; k < subSport.Offering.Lines.length; k++) {
              var loo = subSport.Offering.Lines[k];
              if (loo.GameNum == newLoo.GameNum && loo.PeriodNumber == newLoo.PeriodNumber) {
                if (!isFromSocket) window.updateGameLineData(loo, newLoo, wagerItem.WagerType, wagerItem ? wagerItem.ControlCode : null, true);
                syncLineCircles(loo);
                if (wagerItem) $ticketService.CreateBuyPointsOptions(wagerItem);
                removeEmptyLines();
                found = true;
                return;
              }
            }
          }
        }
      }
    }
    if (!found) {
      var found = false;
      for (var k = 0; k < _sportsAndContestsService.Selections.length; k++) {
        var subSport = _sportsAndContestsService.Selections[k];
        if (subSport.SportSubType.trim() == newLoo.SportSubType && subSport.Lines) {
          for (var k = 0; k < subSport.Lines.length; k++) {
            var loo = subSport.Lines[k];
            if (loo.GameNum == newLoo.GameNum && loo.PeriodNumber == newLoo.PeriodNumber) {
              if (!isFromSocket) window.updateGameLineData(loo, newLoo, wagerItem.WagerType, wagerItem ? wagerItem.ControlCode : null, true);
              syncLineCircles(loo);
              if (wagerItem) $ticketService.CreateBuyPointsOptions(wagerItem);
              removeEmptyLines();
              found = true;
              return;
            }
          }
        }
      }
    }
  };

  _sportsAndContestsService.GamesChanged = function (games) {

  };

  _sportsAndContestsService.AppendContest = function (rawContestData) {
    var selectable, i;
    if (rawContestData.ContestType3 != '.') {
      for (i = 0; _sportsAndContestsService.Selections.length; i++) {
        var selection = _sportsAndContestsService.Selections[i];
        if (selection.ContestType == rawContestData.ContestType && selection.ContestType2 == rawContestData.ContestType2) {
          loadContestLines(rawContestData).then(function () {
            _sportsAndContestsService.Selections.unshift(rawContestData.Offering[0]);
          });
          break;
        }
      }
      return true;
    }
    var newContest = { "SportType": rawContestData.SportType, "ContestType": rawContestData.ContestType, "ContestType2": rawContestData.ContestType2, "ContestTypes2": new Array(), "Selectable": false, "Selected": false, "Type": "C" };
    newContest.ContestTypes2.push({ "SportType": rawContestData.SportType, "ContestType": rawContestData.ContestType, "ContestType2": rawContestData.ContestType2, "Selectable": true, "Selected": false, "Type": "C" });
    for (i = 0; i < _sportsAndContestsService.SportsAndContests.length; i++) {
      var contest = _sportsAndContestsService.SportsAndContests[i];
      if (contest.SportType == rawContestData.SportType) {
        if (rawContestData.SportSubType == null) {
          if (contest.ContestTypes.length > 0) {
            for (var k = 0; k < contest.ContestTypes.length; k++) {
              if (contest.ContestTypes[k].ContestType == rawContestData.ContestType) {
                if (contest.ContestTypes[k].ContestType2 != rawContestData.ContestType2) {
                  selectable = newContest.SportSubType == null && newContest.ContestType2 == null || newContest.ContestType2 == ".";
                  contest.ContestTypes[k].ContestTypes2.push({ "SportType": newContest.SportType, "ContestType": newContest.ContestType, "ContestType2": newContest.ContestType2, "ContestTypes2": new Array(), "Selected": false, "Selectable": selectable, "Type": "C" });
                  UI.Notify($translatorService.Translate("New contest added") + ": " +
                    selectable ? $translatorService.Translate(newContest.ContestType) : $translatorService.Translate(newContest.ContestType2), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
                }
                return true;
              } else if (k == contest.ContestTypes.length - 1) {
                //selectable = newContest.SportSubType == null && (newContest.ContestType2 == null || newContest.ContestType2 == ".");
                contest.ContestTypes.push(newContest);
                UI.Notify($translatorService.Translate("New contest added") + ": " + $translatorService.Translate((newContest.ContestType2 == "." ? newContest.ContestType : newContest.ContestType2)), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
                return true;
              }
            }
          } else {
            UI.Notify($translatorService.Translate("New contest added") + ": " + $translatorService.Translate(newContest.ContestType2), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
            selectable = newContest.SportSubType == null && newContest.ContestType2 == null || newContest.ContestType2 == ".";
            contest.ContestTypes.push({ "SportType": newContest.SportType, "ContestType": newContest.ContestType, "ContestType2": newContest.ContestType, "ContestTypes2": newContest.ContestTypes2, "Selected": false, "Selectable": selectable, "Type": "C" });
          }
        } else {
          for (var j = 0; j < contest.SportSubTypes.length; j++) {
            if (contest.SportSubTypes[j].SportSubType == rawContestData.SportSubType) {
              if (contest.SportSubTypes[j].ContestTypes.length > 0)
                for (var l = 0; l < contest.SportSubTypes[j].ContestTypes.length; l++) {
                  if (contest.SportSubTypes[j].ContestTypes[l].ContestType == rawContestData.ContestType) {
                    UI.Notify($translatorService.Translate("New contest added") + ": " + $translatorService.Translate(newContest.ContestType2), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
                    contest.SportSubTypes[j].ContestTypes[l].ContestTypes2.push(newContest.ContestTypes2[0]);
                    return true;
                  }
                  if (l == contest.SportSubTypes[j].ContestTypes.length - 1) {
                    UI.Notify($translatorService.Translate("New contest added") + ": " + $translatorService.Translate(newContest.ContestType2), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
                    contest.SportSubTypes[j].ContestTypes.push(newContest);
                    return true;
                  }
                }
              else {
                UI.Notify($translatorService.Translate("New contest added") + ": " + $translatorService.Translate(newContest.ContestType2), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
                contest.SportSubTypes[j].ContestTypes.push(newContest);
              }
              return true;
            }
          }
        }
      }
      if (i == _sportsAndContestsService.SportsAndContests.length - 1) {
        _sportsAndContestsService.CreateNewSportsAndContestsRow(rawContestData);
        break;
      }
    }
    return true;
  };

  _sportsAndContestsService.AppendLeague = function (i, data) {

    if (_sportsAndContestsService.SportsAndContests[i].SportType == data.SportType) {
      for (var j = 0; j < _sportsAndContestsService.SportsAndContests[i].SportSubTypes.length; j++) {
        if (_sportsAndContestsService.SportsAndContests[i].SportSubTypes[j].SportSubType == data.SportSubType) return;
      }
      _sportsAndContestsService.SportsAndContests[i].SportSubTypes.push({
        "SportSubType": data.SportSubType,
        "SequenceNumber": data.SequenceNumber,
        "ContestTypes": new Array(),
        "Selected": false,
        "Selectable": true,
        "Type": "G"
      });
      UI.Notify($translatorService.Translate("New league added") + ": " + $translatorService.Translate(_sportsAndContestsService.SportsAndContests[i]
        .SportSubTypes[_sportsAndContestsService.SportsAndContests[i].SportSubTypes.length - 1].SportSubType), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
    }
    $rootScope.safeApply();
  };

  _sportsAndContestsService.LeagueChange = function (leagues) {

    if (leagues.activeLeagues.length > 0) {
      var groupedData = groupSportsAndContests(leagues.activeLeagues);
      modifyPeriod(leagues.activeLeagues)
      modifyLeagueOrSport(groupedData);
      //modifyContestOrSport(groupedData);

    }
    $rootScope.safeApply();
  }

  function modifyPeriod(data) {
    if (_sportsAndContestsService.Selections.length > 0) {
      for (var j = 0; j < data.length; j++) {
        for (var i = 0; i < _sportsAndContestsService.Selections.length; i++) {
          var selection = _sportsAndContestsService.Selections[i];
          if (selection.SportType == data[j].SportType && selection.SportSubType == data[j].SportSubType) {
            for (var k = 0; k < selection.Periods.length; k++) {
              if (selection.Periods[k].PeriodNumber == data[j].PeriodNumber) break;
              if (k == selection.Periods.length - 1) {
                loadSportLines(selection, selection, data[j].PeriodNumber);
                return;
              }
            }
          }
        }
      }
    }

    if (_sportsAndContestsService.Selections.length > 0) {
      for (var i = 0; i < _sportsAndContestsService.Selections.length; i++) {
        var selection = _sportsAndContestsService.Selections[i];
        for (var k = 0; k < selection.Periods.length; k++) {
          var found = false;
          for (var j = 0; j < data.length; j++) {
            if (data[j].SportType == _sportsAndContestsService.Selections[i].SportType && data[j].SportSubType == _sportsAndContestsService.Selections[i].SportSubType) {
              if (selection.Periods[k].PeriodNumber == data[j].PeriodNumber) {
                found = true;
                break;
              }
            }
          }
          if (!found) {
            _sportsAndContestsService.Selections[i].Periods.splice(k, 1);
            return;
          }
        }



      }
    }
  }

  function modifyLeagueOrSport(data) {
    if ($wagerTypesService.IsStraightBet()) {
      for (var j = 0; j < data.length; j++) {
        var found = false;
        for (var i = 0; i < _sportsAndContestsService.SportsAndContests.length; i++) {
          if (data[j].SportType == _sportsAndContestsService.SportsAndContests[i].SportType) {
            found = true;
            for (var l = 0; l < data[j].SportSubTypes.length; l++) {
              var newOne = data[j].SportSubTypes[l].SportSubType;
              for (var k = 0; k < _sportsAndContestsService.SportsAndContests[i].SportSubTypes.length; k++) {
                var current = _sportsAndContestsService.SportsAndContests[i].SportSubTypes[k].SportSubType;
                if (current == newOne) break;
                if (k == _sportsAndContestsService.SportsAndContests[i].SportSubTypes.length - 1) {
                  _sportsAndContestsService.SportsAndContests[i].SportSubTypes.push(data[j].SportSubTypes[l]);
                  //UI.Notify($translatorService.Translate("League added") + ": " + $translatorService.Translate(newOne), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
                  return;
                }
              }
            }
          }
        }
        if (!found) {
          _sportsAndContestsService.SportsAndContests.push(data[j]);
          //UI.Notify($translatorService.Translate("Sport added") + ": " + $translatorService.Translate(data[j].SportType), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
          return;
        }
      }
    }

    for (var j = 0; j < _sportsAndContestsService.SportsAndContests.length; j++) {
      var found = false;
      for (var i = 0; i < data.length; i++) {
        if (_sportsAndContestsService.SportsAndContests[j].SportType == data[i].SportType) {
          found = true;
          for (var l = 0; l < _sportsAndContestsService.SportsAndContests[j].SportSubTypes.length; l++) {
            var newOne = _sportsAndContestsService.SportsAndContests[j].SportSubTypes[l].SportSubType;
            for (var k = 0; k < data[i].SportSubTypes.length; k++) {
              var current = data[i].SportSubTypes[k].SportSubType;
              if (current == newOne) break;
              if (k == data[i].SportSubTypes.length - 1) {
                if (_sportsAndContestsService.SportsAndContests[j].SportSubTypes[l].Selected)
                  _sportsAndContestsService.ToggleSubSport(_sportsAndContestsService.SportsAndContests[j], _sportsAndContestsService.SportsAndContests[j].SportSubTypes[l]);
                _sportsAndContestsService.SportsAndContests[j].SportSubTypes.splice(l, 1);

                //UI.Notify($translatorService.Translate("League removed") + ": " + $translatorService.Translate(newOne), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
                return;
              }
            }
          }
        }
        if (i == data.length - 1 && !found) {
          _sportsAndContestsService.ToggleSubSport(_sportsAndContestsService.SportsAndContests[j], _sportsAndContestsService.SportsAndContests[j].SportSubTypes[0]);
          //UI.Notify($translatorService.Translate("Sport removed") + ": " + $translatorService.Translate(_sportsAndContestsService.SportsAndContests[j].SportType), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
          _sportsAndContestsService.SportsAndContests.splice(j, 1);
          return;
        }
      }
    }
  };

  function modifyContestOrSport(data) {

    for (var j = 0; j < data.length; j++) {
      var found = false;
      for (var i = 0; i < _sportsAndContestsService.SportsAndContests.length; i++) {
        if (data[j].SportType == _sportsAndContestsService.SportsAndContests[i].SportType) {
          found = true;
          var l, k, current, newOne, n, m;
          for (l = 0; l < data[j].ContestTypes.length; l++) {
            if (_sportsAndContestsService.SportsAndContests[i].ContestTypes.length == 0) {
              _sportsAndContestsService.SportsAndContests[i].ContestTypes.push(data[j].ContestTypes[l]);
              //UI.Notify($translatorService.Translate("Contest added") + ": " + $translatorService.Translate(data[j].ContestTypes[l].ContestType), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
              return;
            }
            for (k = 0; k < _sportsAndContestsService.SportsAndContests[i].ContestTypes.length; k++) {
              current = _sportsAndContestsService.SportsAndContests[i].ContestTypes[k].ContestType;
              newOne = data[j].ContestTypes[l].ContestType;
              if (current == newOne || k == _sportsAndContestsService.SportsAndContests[i].ContestTypes.length - 1) {
                if (data[j].ContestTypes[l].ContestTypes2.length > 0) {
                  for (m = 0; m < data[j].ContestTypes[l].ContestTypes2.length; m++) {
                    for (n = 0; n < _sportsAndContestsService.SportsAndContests[i].ContestTypes[k].ContestTypes2.length; n++) {
                      current = _sportsAndContestsService.SportsAndContests[i].ContestTypes[k].ContestTypes2[n].ContestType2;
                      newOne = data[j].ContestTypes[l].ContestTypes2[m].ContestType2;
                      if (current == newOne) break;
                      if (n == _sportsAndContestsService.SportsAndContests[i].ContestTypes[k].ContestTypes2.length - 1) {
                        _sportsAndContestsService.SportsAndContests[i].ContestTypes[k].ContestTypes2.push(data[j].ContestTypes[l].ContestTypes2[m]);
                        //UI.Notify($translatorService.Translate("Contest added") + ": " + $translatorService.Translate(newOne), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
                        return;
                      }
                    }
                  }
                } else {
                  current = _sportsAndContestsService.SportsAndContests[i].ContestTypes[k].ContestType;
                  newOne = data[j].ContestTypes[l].ContestType;
                  if (current == newOne) break;
                  if (k == _sportsAndContestsService.SportsAndContests[i].ContestTypes.length - 1) {
                    _sportsAndContestsService.SportsAndContests[i].ContestTypes.push(data[j].ContestTypes[l]);
                    //UI.Notify($translatorService.Translate("Contest added") + ": " + $translatorService.Translate(newOne), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
                    return;
                  }
                }
              }
            }
          }
          for (l = 0; l < data[j].SportSubTypes.length; l++) {
            if (data[j].SportSubTypes[l].ContestTypes.length == 0) continue;
            var anyContest = true;
            for (n = 0; n < data[j].SportSubTypes[l].ContestTypes.length; n++) {
              for (k = 0; k < _sportsAndContestsService.SportsAndContests[i].SportSubTypes.length; k++) {
                if (data[j].SportSubTypes[l].SportSubType != _sportsAndContestsService.SportsAndContests[i].SportSubTypes[k].SportSubType) continue;
                if (_sportsAndContestsService.SportsAndContests[i].SportSubTypes[k].ContestTypes.length == 0) {
                  _sportsAndContestsService.SportsAndContests[i].SportSubTypes[k].ContestTypes.push(data[j].SportSubTypes[l].ContestTypes[n]);
                  //UI.Notify($translatorService.Translate("Contest added") + ": " + $translatorService.Translate(data[j].SportSubTypes[l].ContestTypes[n].ContestType), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
                  return;
                }

                for (m = 0; m < _sportsAndContestsService.SportsAndContests[i].SportSubTypes[k].ContestTypes.length; m++) {
                  if (_sportsAndContestsService.SportsAndContests[i].SportSubTypes[k].ContestTypes[m].ContestType == data[j].SportSubTypes[l].ContestTypes[n].ContestType) {
                    if (_sportsAndContestsService.SportsAndContests[i].SportSubTypes[k].ContestTypes[m].ContestTypes2.length > 0) {
                      for (var p = 0; p < data[j].SportSubTypes[l].ContestTypes[n].ContestTypes2.length; p++) {
                        for (var q = 0; q < _sportsAndContestsService.SportsAndContests[i].SportSubTypes[k].ContestTypes[m].ContestTypes2.length; q++) {
                          current = _sportsAndContestsService.SportsAndContests[i].SportSubTypes[k].ContestTypes[m].ContestTypes2[q].ContestType2;
                          newOne = data[j].SportSubTypes[l].ContestTypes[n].ContestTypes2[p].ContestType2;
                          if (current == newOne) break;
                          if (q == _sportsAndContestsService.SportsAndContests[i].SportSubTypes[k].ContestTypes[m].ContestTypes2.length - 1) {
                            _sportsAndContestsService.SportsAndContests[i].SportSubTypes[k].ContestTypes[m].ContestTypes2.push(data[j].SportSubTypes[l].ContestTypes[n].ContestTypes2[p]);
                            //UI.Notify($translatorService.Translate("Contest added") + ": " + $translatorService.Translate(newOne), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
                            return;
                          }
                        }
                      }
                    } else {
                      anyContest = true;
                      current = _sportsAndContestsService.SportsAndContests[i].SportSubTypes[k].ContestTypes[m].ContestType2;
                      newOne = data[j].SportSubTypes[l].ContestTypes[n].ContestType2;
                      if (current == newOne) break;
                      var ll = _sportsAndContestsService.SportsAndContests[i].SportSubTypes[k].ContestTypes;
                      if (m == ll.length - 1) {
                        _sportsAndContestsService.SportsAndContests[i].SportSubTypes[k].ContestTypes.push(data[j].SportSubTypes[l].ContestTypes[n]);
                        //UI.Notify($translatorService.Translate("Contest added") + ": " + $translatorService.Translate(newOne), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
                        return;
                      }
                    }
                  }
                }
              }
            }
            if (!anyContest && l == data[j].SportSubTypes.length - 1) {
              _sportsAndContestsService.SportsAndContests[i].SportSubTypes.push(data[j].SportSubTypes[l]);
              //UI.Notify($translatorService.Translate("Contest added") + ": " + $translatorService.Translate(data[j].SportType), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
              return;
            }
          }
        }
      }
      if (!found) {
        _sportsAndContestsService.SportsAndContests.push(data[j]);
        //UI.Notify($translatorService.Translate("Sport added") + ": " + $translatorService.Translate(data[j].SportType), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
        return;
      }
    }


    for (var j = 0; j < _sportsAndContestsService.SportsAndContests.length; j++) {
      var found = false;
      for (var i = 0; i < data.length; i++) {
        if (_sportsAndContestsService.SportsAndContests[j].SportType == data[i].SportType) {
          found = true;
          var l, k, current, newOne, n, m;
          for (l = 0; l < _sportsAndContestsService.SportsAndContests[j].ContestTypes.length; l++) {
            if (data[i].ContestTypes.length == 0) {
              if (_sportsAndContestsService.SportsAndContests[j].ContestTypes[l].Selected)
                _sportsAndContestsService.ToggleContest(data[i].ContestTypes[k]);
              //UI.Notify($translatorService.Translate("Contest removed") + ": " + $translatorService.Translate(_sportsAndContestsService.SportsAndContests[j].ContestTypes[0].ContestType), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
              _sportsAndContestsService.SportsAndContests[j].ContestTypes.splice(l, 1);
              return;
            }
            for (k = 0; k < data[i].ContestTypes.length; k++) {
              current = data[i].ContestTypes[k].ContestType;
              newOne = _sportsAndContestsService.SportsAndContests[j].ContestTypes[l].ContestType;
              if (current == newOne) {
                if (_sportsAndContestsService.SportsAndContests[j].ContestTypes[l].ContestTypes2.length > 0) {
                  for (m = 0; m < _sportsAndContestsService.SportsAndContests[j].ContestTypes[l].ContestTypes2.length; m++) {
                    for (n = 0; n < data[i].ContestTypes[k].ContestTypes2.length; n++) {
                      current = data[i].ContestTypes[k].ContestTypes2[n].ContestType2;
                      newOne = _sportsAndContestsService.SportsAndContests[j].ContestTypes[l].ContestTypes2[m].ContestType2;
                      if (current == newOne) break;
                      if (n == data[i].ContestTypes[k].ContestTypes2.length - 1) {
                        if (_sportsAndContestsService.SportsAndContests[j].ContestTypes[l].ContestTypes2[m].Selected)
                          _sportsAndContestsService.ToggleContest(data[i].ContestTypes[k].ContestTypes2[n]);
                        _sportsAndContestsService.SportsAndContests[j].ContestTypes[l].ContestTypes2.splice(m, 1);
                        //UI.Notify($translatorService.Translate("Contest removed") + ": " + $translatorService.Translate(newOne), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
                        return;
                      }

                    }
                  }
                  if (data[i].ContestTypes[k].ContestTypes2.length == 0) {
                    //UI.Notify($translatorService.Translate("Contest removed") + ": " + $translatorService.Translate(data[i].ContestTypes[k].ContestType), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
                    _sportsAndContestsService.SportsAndContests[j].ContestTypes.splice(l, 1);
                    return;
                  }
                } else {
                  _sportsAndContestsService.SportsAndContests[j].ContestTypes.splice(l, 1);
                  //UI.Notify($translatorService.Translate("Contest removed") + ": " + $translatorService.Translate(newOne), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
                  return;
                }
              }

            }

          }

          for (l = 0; l < _sportsAndContestsService.SportsAndContests[j].SportSubTypes.length; l++) {
            var anyContest = false;
            if (_sportsAndContestsService.SportsAndContests[j].SportSubTypes[l].ContestTypes.length == 0) continue;
            for (n = 0; n < _sportsAndContestsService.SportsAndContests[j].SportSubTypes[l].ContestTypes.length; n++) {
              for (k = 0; k < data[i].SportSubTypes.length; k++) {
                current = data[i].SportSubTypes[k].SportSubType;
                newOne = _sportsAndContestsService.SportsAndContests[j].SportSubTypes[l].SportSubType;
                if (current == newOne || l == _sportsAndContestsService.SportsAndContests[j].SportSubTypes.length - 1) {

                  if (data[i].SportSubTypes[k].ContestTypes.length == 0) {

                    if (_sportsAndContestsService.SportsAndContests[j].SportSubTypes[l].ContestTypes[n].Selected)
                      _sportsAndContestsService.ToggleContest(_sportsAndContestsService.SportsAndContests[j].SportSubTypes[l].ContestTypes[n]);
                    //UI.Notify($translatorService.Translate("Contest removed") + ": " + $translatorService.Translate(_sportsAndContestsService.SportsAndContests[j].SportSubTypes[l].ContestTypes[n].ContestType), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
                    _sportsAndContestsService.SportsAndContests[j].SportSubTypes[l].ContestTypes.splice(n, 1);
                    return;
                  }

                  for (m = 0; m < data[i].SportSubTypes[k].ContestTypes.length; m++) {

                    if (data[i].SportSubTypes[k].ContestTypes[m].ContestTypes2.length > 0) {
                      for (var p = 0; p < _sportsAndContestsService.SportsAndContests[j].SportSubTypes[l].ContestTypes[n].ContestTypes2.length; p++) {
                        for (var q = 0; q < data[i].SportSubTypes[k].ContestTypes[m].ContestTypes2.length; q++) {
                          current = data[i].SportSubTypes[k].ContestTypes[m].ContestTypes2[q].ContestType2;
                          newOne = _sportsAndContestsService.SportsAndContests[j].SportSubTypes[l].ContestTypes[n].ContestTypes2[p].ContestType2;
                          if (current == newOne) break;
                          if (q == data[i].SportSubTypes[k].ContestTypes[m].ContestTypes2.length - 1) {
                            if (_sportsAndContestsService.SportsAndContests[j].SportSubTypes[l].ContestTypes[n].ContestTypes2[p].Selected)
                              _sportsAndContestsService.ToggleContest(_sportsAndContestsService.SportsAndContests[j].SportSubTypes[l].ContestTypes[n].ContestTypes2[p]);
                            _sportsAndContestsService.SportsAndContests[j].SportSubTypes[l].ContestTypes[n].ContestTypes2.splice(p, 1);
                            //UI.Notify($translatorService.Translate("Contest removed") + ": " + $translatorService.Translate(newOne), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
                            return;
                          }
                        }
                      }
                    } else {
                      anyContest = true;
                      current = data[i].SportSubTypes[k].ContestTypes[m].ContestType2;
                      newOne = _sportsAndContestsService.SportsAndContests[j].SportSubTypes[l].ContestTypes[n].ContestType2;
                      if (current == newOne) break;
                      if (l == data[i].SportSubTypes.length - 1) {
                        if (data[i].SportSubTypes[k].ContestTypes[m].Selected)
                          _sportsAndContestsService.ToggleContest(data[i].SportSubTypes[k].ContestTypes[m]);
                        _sportsAndContestsService.SportsAndContests[j].SportSubTypes[k].ContestTypes.splice(m, 1);
                        if (!data[i].SportSubTypes[k].Selectable &&
                          data[i].SportSubTypes[k].ContestTypes.length == 0) {
                          _sportsAndContestsService.SportsAndContests[j].SportSubTypes.splice(k, 1);
                        }
                        //UI.Notify($translatorService.Translate("Contest removed") + ": " + $translatorService.Translate(newOne), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
                        return;
                      }
                    }
                  }
                }
              }
            }
          }
          if (data[i].SportSubTypes.length == 0 && data[i].ContestTypes.length == 0) {
            //UI.Notify($translatorService.Translate("Sport removed") + ": " + $translatorService.Translate(data[i].SportType), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
            _sportsAndContestsService.SportsAndContests.splice(j, 1);
            return
          }
        }
        if (i == data.length - 1 && !found) {
          //UI.Notify($translatorService.Translate("Sport removed") + ": " + $translatorService.Translate(_sportsAndContestsService.SportsAndContests[j].SportType), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
          _sportsAndContestsService.SportsAndContests.splice(j, 1);
          return
        }
      }
    }
  };

  _sportsAndContestsService.CreateNewSportsAndContestsRow = function (rawSportsData) {
    var sportsAndContests = groupSportsAndContests([rawSportsData]);
    for (var i = 0; i < sportsAndContests.length; i++) {
      _sportsAndContestsService.SportsAndContests.push(sportsAndContests[i]);
      //UI.Notify($translatorService.Translate("New sport added") + ": " + $translatorService.Translate(sportsAndContests[i].SportType), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
    }
    $rootScope.safeApply();
  };

  _sportsAndContestsService.RemoveContest = function (rawContestData) {
    if (rawContestData.ContestType3 != ".") return true;
    // it can be in the sporttype root, or under a subsportype
    var sportIdx = -1;
    var subSportIdx = -1;

    for (var i = 0; i < _sportsAndContestsService.SportsAndContests.length; i++) {
      if (_sportsAndContestsService.SportsAndContests[i].SportType != rawContestData.SportType)
        continue;
      sportIdx = i;
      var j;
      if (rawContestData.SportSubType == null) {
        loop1: for (j = 0; j < _sportsAndContestsService.SportsAndContests[i].ContestTypes.length; j++) {
          var contestTypes2 = _sportsAndContestsService.SportsAndContests[i].ContestTypes[j].ContestTypes2;
          if (contestTypes2.length == 0 && _sportsAndContestsService.SportsAndContests[i].ContestTypes[j].ContestType2 == '.') {
            if (_sportsAndContestsService.SportsAndContests[i].ContestTypes[j].ContestType2 == rawContestData.ContestType2 &&
              _sportsAndContestsService.SportsAndContests[i].ContestTypes[j].ContestType == rawContestData.ContestType) {
              UI.Notify($translatorService.Translate("Contest removed") + ": " + $translatorService.Translate(rawContestData.ContestType),
                UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
              _sportsAndContestsService.SportsAndContests[i].ContestTypes.splice(j, 1);
            }
          } else {
            for (var l = 0; l < contestTypes2.length; l++) {
              if (typeof contestTypes2[l].Offering == 'undefined') {
                if (contestTypes2[l].ContestType2 != rawContestData.ContestType2)
                  continue;
                UI.Notify($translatorService.Translate("Contest removed in") + ": " + $translatorService.Translate(rawContestData.ContestType2 == "." ? rawContestData.ContestType : rawContestData.ContestType2),
                  UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
                contestTypes2.splice(l, 1);
                if (contestTypes2.length == 0) _sportsAndContestsService.SportsAndContests[i].ContestTypes.splice(j, 1);
                break loop1;
              } else {
                for (var n = 0; contestTypes2[l].Offering.length; n++) {
                  if (contestTypes2[l].Offering[n].ContestType2 != rawContestData.ContestType2 &&
                    contestTypes2[l].Offering[n].ContestType3 != rawContestData.ContestType3)
                    continue;
                  UI.Notify($translatorService.Translate("Contest removed in") + ": " + $translatorService.Translate(rawContestData.ContestType2 == "." ? rawContestData.ContestType : rawContestData.ContestType2),
                    UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
                  contestTypes2[l].Offering.splice(n, 1);
                  if (contestTypes2[l].Offering.length == 0) contestTypes2[l].splice(l, 1);
                  if (contestTypes2.length == 0) _sportsAndContestsService.SportsAndContests[i].ContestTypes.splice(j, 1);
                  break loop1;
                }
              }
            }
          }
        }
      }
      else {
        loop2: for (j = 0; j < _sportsAndContestsService.SportsAndContests[i].SportSubTypes.length; j++) {
          if (_sportsAndContestsService.SportsAndContests[i].SportSubTypes[j].SportSubType != rawContestData.SportSubType)
            continue;
          subSportIdx = j;

          for (var k = 0; k < _sportsAndContestsService.SportsAndContests[i].SportSubTypes[j].ContestTypes.length; k++) {
            if (_sportsAndContestsService.SportsAndContests[i].SportSubTypes[j].ContestTypes[k].ContestType != rawContestData.ContestType &&
              _sportsAndContestsService.SportsAndContests[i].SportSubTypes[j].ContestTypes[k].ContestType2 != rawContestData.ContestType2)
              continue;
            UI.Notify($translatorService.Translate("Contest removed") + ": " + $translatorService.Translate(rawContestData.ContestType2 == "." ? rawContestData.ContestType : rawContestData.ContestType2),
              UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
            _sportsAndContestsService.SportsAndContests[sportIdx].SportSubTypes[subSportIdx].ContestTypes.splice(k, 1);
            break loop2;
          }
        }
      }
      if (_sportsAndContestsService.SportsAndContests[i].SportSubTypes.length == 0 && _sportsAndContestsService.SportsAndContests[i].ContestTypes.length == 0) _sportsAndContestsService.SportsAndContests.splice(i, 1);
      for (var x = 0; x < _sportsAndContestsService.Selections.length; x++) {
        var selection = _sportsAndContestsService.Selections[x];
        if (selection.ContestType2 == rawContestData.ContestType2 && selection.ContestType3 == rawContestData.ContestType3) {
          _sportsAndContestsService.Selections.splice(x, 1);
          break;
        }
      }
    }
    $rootScope.safeApply();
    return null;
  };

  _sportsAndContestsService.RemovePeriod = function (periodData) {
    angular.forEach(_sportsAndContestsService.Selections, function (selection) {
      if (selection.SportType == periodData.SportType && selection.SportSubType == periodData.SportSubType) {
        var periodIdx = -1;

        for (var i = 0; i < selection.Periods.length; i++) {
          if (selection.Periods[i].PeriodNumber != periodData.PeriodNumber)
            continue;
          periodIdx = i;
          break;
        }
        if (periodIdx >= 0) {
          UI.Notify($translatorService.Translate("Period removed to") + ": " + $translatorService.Translate(selection.SportSubType), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
          selection.Periods.splice(periodIdx, 1);
          $rootScope.safeApply();
        }
      }
    });
  };

  _sportsAndContestsService.RemoveSportsAndContestsRow = function (rawsportData) {

    for (var i = 0; _sportsAndContestsService.SportsAndContests.length > i; i++) {
      var sc = _sportsAndContestsService.SportsAndContests[i];
      if (rawsportData.length == 0) {
        for (var j = 0; sc.SportSubTypes.length > j; j++) {
          if (!sc.SportSubTypes[j].ContestTypes || sc.SportSubTypes[j].ContestTypes.length == 0) {
            sc.SportSubTypes.splice(j, 1);
            j--;
          }
        };
      }
      rawsportData.forEach(function (d) {
        var found = false;
        d.SportSubTypes.forEach(function (ds) {
          if (d.SportType == sc.SportType) {
            found = true;
            sc.SportSubTypes.forEach(function (sst, indexB) {
              if (ds.SportSubType == sst.SportSubType)
                return;
              if (indexB == sc.SportSubTypes.length - 1) {
                UI.Notify($translatorService.Translate("SubSport removed") + ": " +
                  $translatorService.Translate(sst.SportSubType), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
                sc.SportSubTypes.splice(indexB, 1);
              }
            });
          }
          if (!found) {
            for (var j = 0; sc.SportSubTypes.length > j; j++) {
              if (sc.SportSubTypes[j].ContestTypes.length == 0) {
                sc.SportSubTypes.splice(j, 1);
                j--;
              }
            }
          }
        });
      });
      if (sc.SportSubTypes.length == 0 && (!sc.ContestTypes || sc.ContestTypes.length == 0)) {
        UI.Notify($translatorService.Translate("Sport removed") + ": " +
          $translatorService.Translate(sc.SportType), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
        _sportsAndContestsService.SportsAndContests.splice(i, 1);
        i--;
        continue;
      }
    }

    $rootScope.safeApply();
  }

  _sportsAndContestsService.RemoveLeague = function (rawLeagueData) {
    var sportIdx = -1;
    var subSportIdx = -1;

    for (var i = 0; i < _sportsAndContestsService.SportsAndContests.length; i++) {
      if (_sportsAndContestsService.SportsAndContests[i].SportType != rawLeagueData.SportType)
        continue;
      sportIdx = i;

      for (var j = 0; j < _sportsAndContestsService.SportsAndContests[i].SportSubTypes.length; j++) {
        if (_sportsAndContestsService.SportsAndContests[i].SportSubTypes[j].SportSubType != rawLeagueData.SportSubType)
          continue;
        subSportIdx = j;
        break;
      }
      break;
    }
    if (sportIdx >= 0 && subSportIdx >= 0) {
      UI.Notify($translatorService.Translate("League removed") + ": " + $translatorService.Translate(_sportsAndContestsService.SportsAndContests[sportIdx].SportSubTypes[subSportIdx].SportSubType), UI.Position.Top, UI.Position.Center, 200, UI.Type.Warning);
      _sportsAndContestsService.SportsAndContests[sportIdx].SportSubTypes.splice(subSportIdx, 1);
      $rootScope.safeApply();
    }
  };

  function refreshSportLines(sport, subSport) {
    if (subSport.Type == 'G') {

      // //deselect sport
      unbindGameLines(sport, subSport);
      if (!$ticketService.SportHasWagersSelected(sport.SportType, subSport.SportSubType))
        subSport.Offering = null;

      // $rootScope.$broadcast('sportUnsubscribed', {
      //   "SportType": sport.SportType,
      //   "SportSubType": subSport.SportSubType
      // });

      //select again
      $rootScope.LinesLoading = true;
      return loadSportLines(sport, subSport, null).then(function () {
        bindGameLines(subSport);

        if (!subSport.Offering) subSport.Selected = false;
        $rootScope.$broadcast('sportSubscribed', {
          "SportType": sport.SportType,
          "SportSubType": subSport.SportSubType
        });
      });
    } else {

    }
  }

  function ToggleSubSport(sport, subSport, isSpotlight) {
    //subSport.Selected = !subSport.Selected;
    isSpotlight = typeof isSpotlight != 'undefined' ? isSpotlight : false;
    if (!$rootScope.ViewsManager.IsSportView(true)) return;
    if (!isSpotlight) {
      if (!isSportSelected(sport.SportType, subSport.SportSubType)) {
        $rootScope.LinesLoading = true;
        return loadSportLines(sport, subSport, null).then(function () {
        bindGameLines(subSport);
        if (!subSport.Offering) subSport.Selected = false;

        $rootScope.$broadcast('sportSubscribed', {
          "SportType": sport.SportType,
          "SportSubType": subSport.SportSubType
        });
        });
      } else {
        unbindGameLines(sport, subSport);
        if (!$ticketService.SportHasWagersSelected(sport.SportType, subSport.SportSubType))
          subSport.Offering = null;
        if (subSport.Selected) subSport.Selected = false;
        $rootScope.$broadcast('sportUnsubscribed', {
          "SportType": sport.SportType,
          "SportSubType": subSport.SportSubType
        });
      }
    } else {
      var i = 0;
      while (i < _sportsAndContestsService.Selections.length && _sportsAndContestsService.Selections.length > 0)
        if (_sportsAndContestsService.Selections[i].IsSpotlight) {
          if (_sportsAndContestsService.Selections[i].Type == "G" &&
            !$ticketService.SportHasWagersSelected(_sportsAndContestsService.Selections[i].SportType, _sportsAndContestsService.Selections[i].SportSubType)) {
            $rootScope.$broadcast('sportUnsubscribed', {
              "SportType": _sportsAndContestsService.Selections[i].SportType,
              "SportSubType": _sportsAndContestsService.Selections[i].SportSubType
            });

          }
          _sportsAndContestsService.Selections.splice(i, 1);
          i = 0;
        } else i++;
    }
  };

  _sportsAndContestsService.ShowContestByCorrelation = function (gameLine) {
    if (gameLine.Offering != null) return null;
    return loadContestLinesByCorrelation(gameLine).then(function () {
      if (!gameLine.Correlation) return;
    });
  };

  _sportsAndContestsService.ShowContest = function (contest) {
    if (contest.Offering != null) return null;
    return loadContestLines(contest).then(function () {
      if (contest.Offering != null) bindContestLines(contest);
      else contest.Selected = false;
      $rootScope.$broadcast('contestSubscribed', {
        "ContestType": contest.ContestType,
        "ContestType2": contest.ContestType2
      });
    });
  };

  _sportsAndContestsService.HideContestByCorrelation = function (gameLine) {
    if (gameLine.Correlation == null) return;
    $rootScope.$broadcast('contestUnsubscribed', {
      "ContestType": gameLine.Correlation.Offering.ContestType,
      "ContestType2": gameLine.Correlation.Offering.ContestType2
    });
  };

  _sportsAndContestsService.HideContest = function (contest) {
    if (contest.Offering == null) return;
    unbindContestLines(contest);
    if (!contest.Offering) contest.Selected = false;
    $rootScope.$broadcast('contestUnsubscribed', {
      "ContestType": contest.ContestType,
      "ContestType2": contest.ContestType2
    });
  };

  function ShowSubSport(sport, subSport) {
    if (subSport.Offering != null) return null;
    loadSportLines(sport, subSport, null).then(function () {
    bindGameLines(subSport);
    if (!sport.Offering) sport.Selected = false;
    $rootScope.$broadcast('sportSubscribed', {
      "SportType": sport.SportType,
      "SportSubType": subSport.SportSubType
    });
    });


  };

  _sportsAndContestsService.HideSubSport = function (sport, subSport) {
    if (subSport.Offering == null) return;
    unbindGameLines(sport, subSport);
    if (!$ticketService.SportHasWagersSelected(sport.SportType, subSport.SportSubType))
      subSport.Offering = null;
    $rootScope.$broadcast('sportUnsubscribed', {
      "SportType": sport.SportType,
      "SportSubType": subSport.SportSubType
    });
  };

  _sportsAndContestsService.ToggleContest = function (contest) {
    if (!$rootScope.ViewsManager.IsSportView(true) || !$wagerTypesService.IsStraightBet())
      return;
    if (!contest.Offering) {
      _sportsAndContestsService.ShowContest(contest);
    } else {
      _sportsAndContestsService.HideContest(contest);
    }
  };

  _sportsAndContestsService.ToggleContestByCorrelation = function (gameLine) {
    if (!$rootScope.ViewsManager.IsSportView(true) || !$wagerTypesService.IsStraightBet())
      return;
    if (gameLine.Correlation) {
      gameLine.Correlation = null;
      return;
    }
    _sportsAndContestsService.ShowContestByCorrelation(gameLine);

  };

  _sportsAndContestsService.SpotlightContest = function () {
    if (!$rootScope.ViewsManager.IsSportView(true) || !$wagerTypesService.IsStraightBet())
      return;
    loadSpotlightContests().then(function (result) {
      if (result == null) return;
      var response = result;
      if (response == null || response.length == 0) {
        $rootScope.spotlight.ConstestStatus = false;
        return;
      }
      var contest = {
        Offering: groupContests(response)
      };
      bindContestLines(contest, true);
      $rootScope.spotlight.Switch = true;
      $rootScope.$broadcast('contestSubscribed', {
        "ContestType": contest.Offering[0].ContestType,
        "ContestType2": contest.Offering[0].ContestType2
      });
    });
  };

  _sportsAndContestsService.SpotlightGame = function () {
    if (!$rootScope.ViewsManager.IsSportView(true) || !$wagerTypesService.IsStraightBet())
      return;
    loadSpotlightSportLines().then(function (result) {
      if (result == null) return;
      var response = result;
      if (response == null || response.length == 0) {
        $rootScope.spotlight.GameStatus = false;
        return;
      }
      $rootScope.spotlight.Switch = true;
      var tempResponse = [];
      for (var i = 0; i < response.length; i++) {
        var anchor;
        //response[i].SportSubType = "Spotlight/" + response[i].SportSubType;
        tempResponse.push(response[i]);
        if (response.length - 1 == i || (response[i + 1].SportSubType != response[i].SportSubType)) {
          var currentGame = {
            Offering: groupSportLines(tempResponse)
          };
          currentGame.Offering.IsSpotlight = true;
          bindGameLines(currentGame);
          $rootScope.$broadcast('sportSubscribed', {
            "SportType": response[i].SportType,
            "SportSubType": response[i].SportSubType
          });
          setTimeout(function () {
            var selection = response[0];
            if (subSportInSelection(selection)) {
              anchor = "#divSubSport_" + response[0].SportSubTypeId;
              $('#lineDiv').animate({
                scrollTop: $('#lineDiv').scrollTop() + $(anchor).offset().top - 100
              }, 'fast');
            };
          }, 500);
          tempResponse = [];
        }
      };
    });
  };

  _sportsAndContestsService.GetActiveTeasers = function () {
    return _caller.POST({}, 'GetActiveTeasers').then(function (response) {
      _sportsAndContestsService.Teasers = response;
      //Si no existe un teaserSelected.. revisa si hay Default || 0;
      var TeaserIndex=0;
      if(!$ticketService.Ticket.TeaserName){
          if($rootScope.UISettings && $rootScope.UISettings.TeaserDefault){
            var tmpIndex =  _sportsAndContestsService.Teasers.findIndex((teaser)=> teaser.TeaserName.trim() == $rootScope.UISettings.TeaserDefault);
            TeaserIndex = tmpIndex == -1 ? 0 : tmpIndex;
          }
      }

      var teaserName = $ticketService.Ticket.TeaserName || (response.length ? response[TeaserIndex].TeaserName : "");
      $ticketService.ChangeTeaserName(teaserName);
    });
  };

  function sportsAndContestsLoaded(response) {
    _sportsAndContestsService.SportsAndContests = groupSportsAndContests(response);
    $rootScope.$broadcast('SportsAndContestsLoaded');
    return true;
  }

  _sportsAndContestsService.GetActiveSportsAndContests = function (getInactiveSports) {
    return _caller.POST({ getInactiveSports: getInactiveSports }, 'GetSports').then(function (response) {
            if (!$customerService.IsWageringDisabled()) {
      return sportsAndContestsLoaded(response);
            }
    });
  };

  _sportsAndContestsService.GetTeaserSports = function (teaserName) {
    return _caller.POST({ teaserName: teaserName }, 'GetTeaserSports').then(function (response) {
      _sportsAndContestsService.Selections = [];
            if (!$customerService.IsWageringDisabled()) {
      return sportsAndContestsLoaded(response);
            }
    });
  };


  _sportsAndContestsService.RemoveWagerSelections = function () {
    _sportsAndContestsService.Selections = [];
  };

  _sportsAndContestsService.UpdateLines = function (lChanges) { // adjust: linechanges are the real lines now
    if (!lChanges.length) {
      var t = lChanges;
      lChanges = [];
      lChanges.push(t);
    }
    for (var i = 0; i < lChanges.length; i++) {
      var lChanged = lChanges[i];
      if (lChanged.Store.trim() != $customerService.Info.Store.trim()) continue;
      for (var x = 0; x < _sportsAndContestsService.Selections.length; x++) {
        var selection = _sportsAndContestsService.Selections[x];
        if (lChanged.ContestantNum > 0) {
          if (selection.Type == "C" && selection.ContestType == lChanged.ContestType && selection.ContestType2 == lChanged.ContestType2 && selection.ContestType3 == lChanged.ContestType3) {
            contestLineUpdate(lChanged, selection);
          }
        } else {
          if (selection.Type == "G" && selection.Lines && selection.Lines.length && selection.SportType.trim() == lChanged.SportType.trim() && selection.SportSubType.trim() == lChanged.SportSubType.trim()) {
            gameLineUpdate(lChanged, selection);
          }
        }
      }
    }
  };

  function AutoSelection() {
    let tempSelectionlist = [...$ticketService.offeringSelectedItems];
    $ticketService.offeringSelectedItems = [];
    for (let i = 0; i < tempSelectionlist.length; i++) {
      let wagerItem = tempSelectionlist[i];
      let data = {
        Sport: { SportType: wagerItem.gameItem.SportType },
        SubSport: { SportSubType: wagerItem.gameItem.SportSubType },
        GameNum: wagerItem.gameItem.GameNum
      }
      loadSportLines(data.Sport, data.SubSport, null, data.GameNum).then(function () {
        if (!data.SubSport.Offering) return;
      wagerItem.actualgameItem = data.SubSport.Offering.Lines.find(gameItem =>
        gameItem.GameNum == wagerItem.gameItem.GameNum && gameItem.PeriodNumber == wagerItem.gameItem.PeriodNumber && gameItem.IsTitle == 0 &&
        gameItem.SportType == wagerItem.gameItem.SportType && gameItem.SportSubType == wagerItem.gameItem.SportSubType);

      if (wagerItem.actualgameItem) {
          $ticketService.GameLineAction(wagerItem.actualgameItem, wagerItem.subWagerType, wagerItem.teamPos, wagerItem.wageringDisabled, wagerItem.sportsWageringDisabled, wagerItem.isDemo).then();
      }
      });

    }
  }

  function fixSelectionOnSubSport() {
      for (let selectionIndex = 0; selectionIndex < _sportsAndContestsService.Selections.length; selectionIndex++) {
    for (let i = 0; i < $ticketService.Ticket.WagerItems.length; i++) {
      let wagerItem = $ticketService.Ticket.WagerItems[i];
              let lines = _sportsAndContestsService.Selections[selectionIndex].Lines;
              if (lines) {
                  let gameLineIdx = lines.findIndex(gameItem =>
        gameItem.GameNum == wagerItem.Loo.GameNum && gameItem.PeriodNumber == wagerItem.Loo.PeriodNumber && gameItem.IsTitle == 0 &&
        gameItem.SportType == wagerItem.Loo.SportType && gameItem.SportSubType == wagerItem.Loo.SportSubType);
      if (gameLineIdx >= 0) {
                      lines[gameLineIdx].Spread1Selected = wagerItem.Loo.Spread1Selected == true || lines[gameLineIdx].Spread1Selected == true;
                      lines[gameLineIdx].Spread2Selected = wagerItem.Loo.Spread2Selected == true || lines[gameLineIdx].Spread2Selected == true
                      lines[gameLineIdx].MoneyLine1Selected = wagerItem.Loo.MoneyLine1Selected == true || lines[gameLineIdx].MoneyLine1Selected == true
                      lines[gameLineIdx].MoneyLine2Selected = wagerItem.Loo.MoneyLine2Selected == true || lines[gameLineIdx].MoneyLine2Selected == true
                      lines[gameLineIdx].MoneyLine3Selected = wagerItem.Loo.MoneyLine3Selected == true || lines[gameLineIdx].MoneyLine3Selected == true
                      lines[gameLineIdx].TotalPoints1Selected = wagerItem.Loo.TotalPoints1Selected == true || lines[gameLineIdx].TotalPoints1Selected == true
                      lines[gameLineIdx].TotalPoints2Selected = wagerItem.Loo.TotalPoints2Selected == true || lines[gameLineIdx].TotalPoints2Selected == true
                      lines[gameLineIdx].Team1TtlPtsAdj1Selected = wagerItem.Loo.Team1TtlPtsAdj1Selected == true || lines[gameLineIdx].Team1TtlPtsAdj1Selected == true
                      lines[gameLineIdx].Team2TtlPtsAdj1Selected = wagerItem.Loo.Team2TtlPtsAdj1Selected == true || lines[gameLineIdx].Team2TtlPtsAdj1Selected == true
                      lines[gameLineIdx].Team1TtlPtsAdj2Selected = wagerItem.Loo.Team1TtlPtsAdj2Selected == true || lines[gameLineIdx].Team1TtlPtsAdj2Selected == true
                      lines[gameLineIdx].Team2TtlPtsAdj2Selected = wagerItem.Loo.Team2TtlPtsAdj2Selected == true || lines[gameLineIdx].Team2TtlPtsAdj2Selected == true
                      wagerItem.Loo = lines[gameLineIdx];
                  }
              }
      }
    }
  }

  _sportsAndContestsService.SearchGame = function (a) {
    return _caller.POST({ wordSearch: a }, 'SearchGame', null, true).then();
  };

  _sportsAndContestsService.GetRifMaxChainSize = function () {
    return _caller.POST({ }, 'GetRifMaxChainSize', null, true).then();
  };

  _sportsAndContestsService.ToggleSubSport = ToggleSubSport;
_sportsAndContestsService.loadCustomProps = loadCustomProps;

  _sportsAndContestsService.ShowSubSport = ShowSubSport;

  _sportsAndContestsService.AutoSelection = AutoSelection;

  _sportsAndContestsService.loadSportLines = loadSportLines;
  _sportsAndContestsService.refreshSportLines = refreshSportLines;

  _sportsAndContestsService.LeagueHasOffering =  function (league){
    var spC = _sportsAndContestsService.SportsAndContests;
    if(!spC.length) return false;

    var sport = spC.filter(function (sport) {
      return sport.SportType == league.SportType &&
          sport.SportSubTypes.some(function (sel) {
            return ((sel.SportSubType == league.SportSubType) );
          });
    });
    return sport.length == 1;
  }

  return _sportsAndContestsService;

}]);
;
appModule.factory('$systemService', ['$http','$rootScope', function ($http,$rootScope) {

  var _caller = new ServiceCaller($http, 'Config');
  var _systemService = {
    Parameters: null
  };

  //Private Methods

  function getSystemParameters() {
    return _caller.POST({}, 'Get').then(function (result) {
      if(typeof(result.HideRotationNumbers) == "undefined"){
        result.HideRotationNumbers = true;
      }
      _systemService.Parameters = result;
      $rootScope.HideRotationNumbers = _systemService.Parameters.HideRotationNumbers;
        if (_systemService.Parameters.ParlayPayCardSports)
            ParlayFunctions.PayCardSports = _systemService.Parameters.ParlayPayCardSports

      if (_systemService.Parameters.DecimalOddsPrecision)
        if (!isNaN(_systemService.Parameters.DecimalOddsPrecision)) CommonFunctions.DecimalPrecision = parseInt(_systemService.Parameters.DecimalOddsPrecision);
      else
        CommonFunctions.DecimalPrecision = SETTINGS.DecimalPrecision;
    });
  };

  getSystemParameters();

  return _systemService;

}]);;
appModule.factory('$errorHandler', ['$rootScope', '$http', function ($rootScope, $http) {

  var _caller = new ServiceCaller($http, 'SystemLog');

  var _errorHandler = {};

  _errorHandler.stackLinesToReport = 4;
  _errorHandler.output = "service"; // console, service or screen
  _errorHandler.active = true;
  _errorHandler.appName = "GBSWeb";

  _errorHandler.GetStackLines = function (stack) {
    var strRet = "";
    var stackArray = stack.split("\n");
    this.stackLinesToReport = 4;
    for (var i = 0; i < this.stackLinesToReport; i++) {
      strRet += stackArray[i];
      if (i < this.stackLinesToReport - 1) strRet += "\n";
    }
    return strRet;
  };

  _errorHandler.SubmitError = function (data) {
    var stackTrace = data.Message + "\n" + data.StackLines;
    _caller.POST({ 'appName': _errorHandler.appName, 'stackTrace': stackTrace }, 'AddLog', null, true).then();
  };

  _errorHandler.Error = function (data, method) {
    if (typeof method === "undefined") method = "Undefined";
    if (_errorHandler.active) {
      var stackLines = "";
      var msg = "Method: " + method + ". ";
      if (typeof data == 'string') {
        msg += "str: " + data;
      } else if (data.type != null && data.target != null && data.type === "error") msg += JSON.stringify(data);
      else if (typeof data == 'object') {
        if (data.stack) stackLines = _errorHandler.GetStackLines(data.stack);
        try {
          msg += data.toString();
        } catch (ex) {
        }
      }
      var obj = { StackLines: stackLines, Message: msg };
      if (_errorHandler.output === "console") log(data);
      else if (_errorHandler.output === "screen") alert(data);
      else _errorHandler.SubmitError(obj);
    }
  };

  return _errorHandler;

}]);;
appModule.factory('$webStorageService', [function () {

  var _webStorageService = {
    local: {},
    session: {},
    active: true
  };

  _webStorageService.IsSupported = function () {
    return typeof (Storage) != "undefined";
  };

  _webStorageService.local.setItem = function (item, value) {
    if (!_webStorageService.active) return;
    localStorage[item] = value;
  };

  /*
  * Ej. setWithExpiry("myKey", inputSet.value, 5000)
  * */
  _webStorageService.local.setWithExpiry = function (key, value, ttl){
    const now = new Date()
    // `item` is an object which contains the original value
    // as well as the time when it's supposed to expire
    const item = {
      value: value,
      expiry: now.getTime() + ttl,
    }
    localStorage.setItem(key, JSON.stringify(item))
  }

  /*
    const value = getWithExpiry("myKey")
   basicamente si el key se ha pasado del tiempo configurado, el key se borra
  */
  _webStorageService.local.getWithExpiry = function (key){
    const itemStr = localStorage.getItem(key)
    // if the item doesn't exist, return null
    if (!itemStr) {
      return null
    }
    const item = JSON.parse(itemStr)
    const now = new Date()
    // compare the expiry time of the item with the current time
    if (now.getTime() > item.expiry) {
      // If the item is expired, delete the item from storage
      // and return null
      localStorage.removeItem(key)
      return null
    }
    return item.value
  }

  _webStorageService.local.getItem = function (item) {
    if (!_webStorageService.active) return null;
    return localStorage[item];
  };

  _webStorageService.local.setObject = function (item, object) {
    if (!_webStorageService.active) return;
    localStorage[item] = JSON.stringify(object);
  };

  _webStorageService.local.getObject = function (item) {
    if (!_webStorageService.active) return null;
    var strItem = localStorage[item];
    if (strItem && strItem.length > 0)
      return JSON.parse(strItem);
    else return null;
  };

  _webStorageService.local.removeObject = function (item) {
    if (!_webStorageService.active) return;
    localStorage.removeItem(item);
  };

  _webStorageService.session.removeItem = function (item) {
    if (!_webStorageService.active) return;
    sessionStorage.removeItem(item);
  };

  _webStorageService.session.setItem = function (item, object) {
    if (!_webStorageService.active) return;
    sessionStorage[item] = JSON.stringify(object);
  };

  _webStorageService.session.getItem = function (item) {
    if (!_webStorageService.active) return null;
    var strItem = sessionStorage[item];
    if (strItem && strItem.length > 0)
      return JSON.parse(strItem);
    //return sessionStorage[item];
    return [];
  };

  return _webStorageService;

}]);;
appModule.factory('$integrationService', ['$http', function ($http) {

  var _caller = new ServiceCaller($http, 'Integrations');

    var _integrationService = {
    propsBuilderGames: [],
    ChickenFight: {},
        dragonGamingGames: {},
        pragmaticGames: [],
        ganaCashier: {},
		AsiaGame: {}
    };

    var propsBuilderGamesUrl = 'https://bv2-us.digitalsportstech.com/api/schedule?sb=ticosports-asi';

  _integrationService.GetPropsBuilderGames = function () {
        return $http.get(propsBuilderGamesUrl).then(function (response) {
            _integrationService.propsBuilderGames = response.data.data;
            return response.data.data;
        });
    };

    _integrationService.ChickenFightingDeposit_Credit = function (tranCode, amount) {

    return _caller.POST({ 'tranCode': tranCode, 'amount': amount }, 'ChickenFightingDeposit_Credit').then(function (result) {
      const obj = JSON.parse(result);
      _integrationService.ChickenFight = obj;
      return result;
    });
  }
  
  _integrationService.AsiaGameProcessTransaction = function (amount, tranCode) {
    return _caller.POST({ 'amount': amount, 'tranCode': tranCode }, 'AsiaGameTransferProces').then(function (result) {
        _integrationService.AsiaGame = result;
        return result;
    });
  }

  _integrationService.GetDragonGamingGames = function () {

    return _caller.POST({}, 'GetDragonGamingGames').then(function (result) {
      const obj = JSON.parse(result);
      _integrationService.dragonGamingGames = obj.result;
      return obj.result;

    });
  };

    _integrationService.GetPragmaticGames = function () {

        return _caller.POST({}, 'GetPragmaticGamingGames').then(function (result) {

            _integrationService.pragmaticGames = result;
            return result;

        });
    };

    _integrationService.GanaCashier = function (firstName, lastName, adress, city, state, zip, amount, creditCardNum, creditCardEXP, creditCardCVV) {

        return _caller.POST({
            'firstName': firstName, 'lastName': lastName, 'adress': adress, 'city': city, 'state': state, 'zip': zip, 'amount': amount, 'creditCardNum': creditCardNum
            , 'creditCardEXP': creditCardEXP, 'creditCardCVV': creditCardCVV
        }, 'Cashier').then(function (result) {
            _integrationService.ganaCashier = result;
            return result;

        });
    };

    return _integrationService;

}]);
;
appModule.factory('$encryptionService', ['$http', function ($http) {

  var _caller = new ServiceCaller($http, 'Login', 'CustomerSignIn');

  var _encryption = {};

  _encryption.CustomerPassCheck = function (customerId, password, obsoleteKey) {
    return _caller.POST({ 'customerId': customerId, 'password': password, 'obsoleteKey': obsoleteKey }, 'CheckCustomerPassword', null, true);
  };

  _encryption.CustomerPassUpdate = function (customerId, password, obsoleteKey) {
    return _caller.POST({ 'customerId': customerId, 'password': password, 'obsoleteKey': obsoleteKey }, 'UpdateCustomerPassword', null, true);
  };

  _encryption.CustomerPinUpdate = function (customerId, pin, obsoleteKey) {
    return _caller.POST({ 'customerId': customerId, 'pin': pin, 'obsoleteKey': obsoleteKey }, 'UpdateCustomerPin', null, true);
  };

  _encryption.RequestToken = function () {
    return _caller.POST({}, 'TemporalToken', null, true);
  };

  return _encryption;

}]);
;
appModule.factory('$settingsService', ['$http', '$rootScope', function ($http, $rootScope) {

  var _caller = new ServiceCaller($http, 'Customer');
  var _gbAppVersion = "20150628-2";
  var _settingsService = {};

  _settingsService.Languages = [];
  _settingsService.AvailableHomePages = [];
  _settingsService.BaseballActionTypes = [];
  _settingsService.TimeZones = [];
  _settingsService.MainSports = [];

  _settingsService.GetLanguages = function () {
    return _caller.GET(SETTINGS.LangFilesUrl + '/data/LangFiles.json?v=' + _gbAppVersion).then(function (result) {
      _settingsService.Languages = result.data;
      $rootScope.$broadcast('Languages');
    });

  };

  _settingsService.GetAvailableHomePages = function () {
    _caller.GET(appModule.Root +'/data/HomePages.json?v=' + _gbAppVersion).then(function (result) {
      _settingsService.AvailableHomePages = result.data;
      $rootScope.$broadcast('HomePages');
    });
  };

  _settingsService.GetBaseballActionTypes = function () {
    _caller.GET(appModule.Root +'/data/BaseballAction.json?v=' + _gbAppVersion).then(function (result) {
      _settingsService.BaseballActionTypes = result.data;
      $rootScope.$broadcast('BaseballActions');
    });
  };

  _settingsService.GetTimeZones = function () {
    _caller.GET(appModule.Root +'/data/TimeZones.json?v=' + _gbAppVersion).then(function (result) {
      _settingsService.TimeZones = result.data;
      $rootScope.$broadcast('TimeZones');
    });
  };

  _settingsService.GetMainSports = function () {
    _caller.GET(appModule.Root +'/data/MainSports.json?v=' + _gbAppVersion).then(function (result) {
      _settingsService.MainSports = result.data;
      $rootScope.$broadcast('MainSports');
    });
  };

  _settingsService.GetSidebarBanners = function () {
    _caller.GET(appModule.Root +'/data/sidebarBanners.json?v=' + _gbAppVersion).then(function (result) {
      var today = new Date;
      _settingsService.SidebarBanners = {
        LeftBanners: [],
        RightBanners: []
      };
      for (var i = 0; i < result.data.LeftBanners.length; i++) {
        if (result.data.LeftBanners[i].Active || (Date(result.data.LeftBanners[i].ActiveFrom) < today && Date(result.data.LeftBanners[i].ActiveTo) > today)) _settingsService.SidebarBanners.LeftBanners.push(result.data.LeftBanners[i]);
      }
      for (var i = 0; i < result.data.RightBanners.length; i++) {
        if (result.data.RightBanners[i].Active || (Date(result.data.RightBanners[i].ActiveFrom) < today && Date(result.data.RightBanners[i].ActiveTo) > today)) _settingsService.SidebarBanners.RightBanners.push(result.data.RightBanners[i]);
      }
      $rootScope.$broadcast('SidebarBannersLoaded');
    });
  };

  _settingsService.SaveCustomerSettings = function (language, homePage, sportType, sportSubType, teamId, baseballAction, rememberPassword, customerTimeZone, priceType) {
    return _caller.POST({
      'webLanguage': language,
      'webHomePage': homePage,
      'favoriteSport': sportType,
      'favoriteSportSubType': sportSubType,
      'favoriteTeamId': teamId,
      'baseballAction': baseballAction,
      'webRememberPassword': rememberPassword,
      'custTimeZone': customerTimeZone,
      'priceType': priceType
    }, 'SaveSettings').then(function (result) {
      $rootScope.$broadcast('SettingsSaved');
      return result;
    });
  };

  _settingsService.AutoAcceptSwitch = function (temporal) {
    return _caller.POST({ 'temporal': temporal }, 'ChangeAutoAccept').then(function () {
      return false;
    });
  };

  return _settingsService;


}]);;
appModule.factory('$reportsService', ['$http', function ($http) {

  var _caller = new ServiceCaller($http, 'reports');
  var _reportsService = {};

  _reportsService.DailyFigures = null;
  _reportsService.GroupedOpenBets = [];
  _reportsService.TransactionList = [];
  _reportsService.CasinoTransactionList = [];
  _reportsService.CashTransactionList = [];
  _reportsService.ShowModal = false;

  function transaction(transaction) {
    return {
      Amount: transaction.Amount,
      AmountLost: transaction.AmountLost,
      AmountWagered: transaction.AmountWagered,
      AmountWon: transaction.AmountWon,
      CurrentBalance: transaction.CurrentBalance,
      Comments: transaction.Comments,
      Description: transaction.Description,
      DocumentNumber: transaction.DocumentNumber,
      EnteredBy: transaction.EnteredBy,
      FreePlayFlag: transaction.FreePlayFlag,
      HoldAmount: transaction.HoldAmount,
      ItemWagerType: transaction.ItemWagerType,
      Items: transaction.Items,
      Outcome: transaction.Outcome,
      PeriodDescription: transaction.PeriodDescription,
      ShortDesc: transaction.ShortDesc,
      SportSubType: transaction.SportSubType,
      SportType: transaction.SportType,
      Team1ID: transaction.Team1ID,
      Team1Score: transaction.Team1Score,
      Team2ID: transaction.Team2ID,
      Team2Score: transaction.Team2Score,
      TranCode: transaction.TranCode,
      TranDateTimeString: transaction.TranDateTimeString,
      AcceptedDateTimeString: transaction.AcceptedDateTimeString,
      TranType: transaction.TranType,
      WagerNumber: (transaction.WagerNumber ? '-' + transaction.WagerNumber : ''),
      WagerType: transaction.WagerType,
            WinnerID: transaction.WinnerID,
            ItemDescription: transaction.ItemDescription
    };
  };

  function newWagerItem(wager) {
    return {
      Comments: (wager.Comments == null || wager.Comments == "" ? null : wager.Comments),
      ContinueOnPushFlag: wager.ContinueOnPushFlag,
      Description: wager.Description,
      FreePlayFlag: wager.FreePlayFlag,
      SportType: wager.SportType,
      PeriodDescription: wager.PeriodDescription,
      Team1Score: wager.Team1Score,
      Team2Score: wager.Team2Score,
      Team1ID: wager.Team1ID,
      Team2ID: wager.Team2ID,
      Outcome: (wager.Outcome == "W" ? 'WON' : wager.Outcome == "L" ? 'LOST' : wager.Outcome == "X" ? 'PUSH' : ''),
      Result: (wager.Outcome == "W" || wager.TranType == "W" ? 'WON' : wager.Outcome == "L" || wager.TranType == "L" ? 'LOST' : wager.Outcome == "X" ? 'PUSH' : ''),
      WagerType: wager.WagerType,
      WinnerID: wager.WinnerID,
      EventDateTime: wager.EventDateTime,
      EventDateTimeString: wager.EventDateTimeString,
      GameNum: wager.GameNum,
      PostedDateTimeString: wager.PostedDateTimeString,
      ParlayRestriction: wager.ParlayRestriction,
      CorrelationId: wager.CorrelationId,
      ItemWagerType: wager.ItemWagerType,
      PeriodNumber: wager.PeriodNumber,
      EnteredBy: wager.EnteredBy,
      Amount: wager.Amount,
      AmountWagered: wager.AmountWagered,
      AmountLost: wager.AmountLost,
      AmountWon: wager.AmountWon,
            ARLink: wager.ARLink,
            SystemID: wager.SystemID,
            TranType: wager.TranType
    };
  };

  function createManualItems(fullDescription) {
    var arr = fullDescription.split("|");
    var items = [];
    for (var i = 0; i < arr.length; i++) {
      items.push({ Description: arr[i] });
    }
    return items;
  }


  _reportsService.DisplayWagerTypeName = function (t) {
    var Items = [
      {
        Name: "Contest",
        Code: "C"
      }, {
        Name: "Spread",
        Code: "S"
      }, {
        Name: "Money Line",
        Code: "M"
      }, {
        Name: "Total Points",
        Code: "L"
      }, {
        Name: "Team Totals",
        Code: "E"
      }, {
        Name: "Parlay",
        Code: "P"
      }, {
        Name: "Teaser",
        Code: "T"
      }, {
        Name: "If Bet",
        Code: "I"
      }, {
        Name: "Horses",
        Code: "G"
      }, {
        Name: "Manual Play",
        Code: "A"
      }
    ];
    for (var i = 0; i < Items.length; i++) {
      if (t.WagerType === Items[i].Code) {
        if (t.ARLink == 1 && t.WagerType === 'I') {
          return 'Action Reverse';
        } else if (t.ContinueOnPushFlag && t.WagerType === 'I') {
          return t.ContinueOnPushFlag == 'Y' ? 'If Win or Push' : 'If Win Only';
        }
        else return Items[i].Name + ' ' + (t.WagerType == 'T' && t.TeaserName ? t.TeaserName : '');
      }
    }
    return null;
  };

  _reportsService.GetCustomerDailyFigures = function (customerId, weekOffset, currencyCode) {
    return _caller.POST({ 'customerId': customerId, 'weekOffset': weekOffset, 'currencyCode': currencyCode }, 'GetCustomerDailyFigures').then(function (result) {
      _reportsService.DailyFigures = result;
      if (_reportsService.DailyFigures.ZeroBalance != null)
        _reportsService.DailyFigures.ZeroBalance = CommonFunctions.RoundNumber(_reportsService.DailyFigures.ZeroBalance);
      for (var i = 0; i < _reportsService.DailyFigures.ValuesPerDay.length; i++) {
        _reportsService.DailyFigures.ValuesPerDay[i].ThisDate = CommonFunctions.FormatDateTime(_reportsService.DailyFigures.ValuesPerDay[i].ThisDate, 1, 2); // timezone is temp, fix *

        if (_reportsService.DailyFigures.ValuesPerDay[i].CashInOut != null)
          _reportsService.DailyFigures.ValuesPerDay[i].CashInOut = CommonFunctions.RoundNumber(_reportsService.DailyFigures.ValuesPerDay[i].CashInOut);

        if (_reportsService.DailyFigures.ValuesPerDay[i].WinLoss != null)
          _reportsService.DailyFigures.ValuesPerDay[i].WinLoss = CommonFunctions.RoundNumber(_reportsService.DailyFigures.ValuesPerDay[i].WinLoss);

        if (_reportsService.DailyFigures.ValuesPerDay[i].CasinoWinLoss != null)
          _reportsService.DailyFigures.ValuesPerDay[i].CasinoWinLoss = CommonFunctions.RoundNumber(_reportsService.DailyFigures.ValuesPerDay[i].CasinoWinLoss);
      }
    });
    //actualWeek = weekOffset;
  };

  _reportsService.GetWeeksRange = function () {
    var weeksArray = new Array();
    for (var i = 0; i < 11; i++) {
      weeksArray.push({ DateRange: CommonFunctions.WeekbyDatesRange(i), Index: i });
    }
    return weeksArray;
  };

  _reportsService.GetScores = function (dateTime, weekNum, finalOnly = false) {
    return _caller.POST({ dateTimeS: dateTime, weekNum: weekNum, finalOnly: finalOnly }, 'GetScores', null, true);
  };

  _reportsService.GetCustomerPendingBets = function (customerId, rollingIfBetMode) {
    var groupedItems = null;
    var holdTicketNumber = null;
    var holdWagerNumber = null;
    return _caller.POST({ 'customerId': customerId, 'rollingIfBetMode': !!rollingIfBetMode }, 'GetPendingWagers').then(function (result) {

      var allOpenBets = result;
      var groupedOpenBets = new Array();

      if (allOpenBets != null && allOpenBets.length > 0) {

        groupedOpenBets = new Array();
        groupedItems = new Array();
        holdTicketNumber = allOpenBets[0].TicketNumber;
        holdWagerNumber = allOpenBets[0].WagerNumber;
        for (var i = 0; i < allOpenBets.length; i++) {
          if (holdTicketNumber != allOpenBets[i].TicketNumber || holdWagerNumber != allOpenBets[i].WagerNumber) {
            groupedOpenBets.push(allOpenBets[i - 1]);
            if (allOpenBets[i - 1].WagerType == 'A') {
              groupedOpenBets[groupedOpenBets.length - 1].Items = createManualItems(allOpenBets[i - 1].Description);
            }
            else {
              if (groupedOpenBets.length > 0 && groupedItems != null && groupedItems.length > 0)
                groupedOpenBets[groupedOpenBets.length - 1].Items = groupedItems;
            }
            groupedItems = new Array();
            groupedItems.push(newWagerItem(allOpenBets[i]));
          } else {
            groupedItems.push(newWagerItem(allOpenBets[i]));
          }
          holdTicketNumber = allOpenBets[i].TicketNumber;
          holdWagerNumber = allOpenBets[i].WagerNumber;

          if (i == allOpenBets.length - 1) {
            groupedOpenBets.push(allOpenBets[i]);
            groupedOpenBets[groupedOpenBets.length - 1].Items = groupedItems;
          }
        }
      }

      _reportsService.GroupedOpenBets = groupedOpenBets;
    });
  };

  _reportsService.GetCasinoTransactionsByDate = function (customerId, date) {
    return _caller.POST({ 'customerId': customerId, 'date': date }, 'GetCasinoActionByDate').then(function (result) {
      var casinoTransactions = result;
      if (casinoTransactions != null && casinoTransactions.length > 0) {
        _reportsService.CasinoTransactionList = [];
        for (var i = 0; i < casinoTransactions.length; i++) {
          _reportsService.CasinoTransactionList.push(transaction(casinoTransactions[i]));
        }
      } else {
        _reportsService.CasinoTransactionList = [];
      }
    });
  };

  _reportsService.GetCashTransactionsByDate = function (customerId, date) {
    return _caller.POST({ 'customerId': customerId, 'date': date }, 'GetCashTransactionsByDate').then(function (result) {
      var cashTransactions = result;
      if (cashTransactions != null && cashTransactions.length > 0) {
        _reportsService.CashTransactionList = [];
        for (var i = 0; i < cashTransactions.length; i++) {
          _reportsService.CashTransactionList.push(transaction(cashTransactions[i]));
        }
      } else {
        _reportsService.CashTransactionList = null;
      }
    });
  };

  _reportsService.GetCustomerTransactionByTicketNumber = function (customerId, ticketNumber) {

    var groupedItems = null;
    var holdDocumentNumber = null;
    var holdWagerNumber = null;
    return _caller.POST({ 'customerId': customerId, 'ticketNumber': ticketNumber }, 'GetTransactionsByTicketNumber').then(function (result) {

      var allTransactions = result;
      var groupedTransactions = new Array();
      var accumTran = 0;

      if (allTransactions != null && allTransactions.length > 0) {

        groupedTransactions = new Array();
        groupedItems = new Array();
        holdDocumentNumber = allTransactions[allTransactions.length - 1].DocumentNumber;
        holdWagerNumber = allTransactions[allTransactions.length - 1].WagerNumber;

        for (var i = allTransactions.length - 1; i >= 0; i--) {
          if (holdDocumentNumber != allTransactions[i].DocumentNumber || holdWagerNumber != allTransactions[i].WagerNumber) {
            groupedTransactions.push(allTransactions[i + 1]);
            if (groupedTransactions.length > 0 && groupedItems != null && groupedItems.length > 0)
              groupedTransactions[groupedTransactions.length - 1].Items = groupedItems;
            groupedItems = new Array();
            groupedItems.push(newWagerItem(allTransactions[i]));
            if (i < allTransactions.length - 1) groupedTransactions[groupedTransactions.length - 1].CurrentBalance = groupedTransactions[groupedTransactions.length - 1].CurrentBalance + accumTran;
            accumTran += groupedTransactions[groupedTransactions.length - 1].TranCode == "C" ? groupedTransactions[groupedTransactions.length - 1].Amount * -1 : groupedTransactions[groupedTransactions.length - 1].Amount;


          } else {
            groupedItems.push(newWagerItem(allTransactions[i]));
          }
          holdDocumentNumber = allTransactions[i].DocumentNumber;
          holdWagerNumber = allTransactions[i].WagerNumber;
          if (i == 0) {
            groupedTransactions.push(allTransactions[i]);
            groupedTransactions[groupedTransactions.length - 1].Items = groupedItems;
            groupedTransactions[groupedTransactions.length - 1].CurrentBalance = groupedTransactions[groupedTransactions.length - 1].CurrentBalance + accumTran;
          }
        }
      }
      _reportsService.HookedTransactionList = groupedTransactions;
    });
  };

  _reportsService.GetCustomerTransactionListByDays = function (customerId, numDays,filterType) {

    var groupedItems = null;
    var holdDocumentNumber = null;
    var holdWagerNumber = null;
      return _caller.POST({ 'customerId': customerId, 'numDays': numDays, 'filterType': filterType }, 'GetTransactionsByDays').then(function (result) {

      var allTransactions = result;
      var groupedTransactions = new Array();
      var accumTran = 0;

      if (allTransactions != null && allTransactions.length > 0) {

        groupedTransactions = new Array();
        groupedItems = new Array();
        holdDocumentNumber = allTransactions[allTransactions.length - 1].DocumentNumber;
        holdWagerNumber = allTransactions[allTransactions.length - 1].WagerNumber;

        for (var i = allTransactions.length - 1 ; i >= 0; i--) {
          if (holdDocumentNumber != allTransactions[i].DocumentNumber || holdWagerNumber != allTransactions[i].WagerNumber) {
            groupedTransactions.push(allTransactions[i + 1]);
            if (groupedTransactions.length > 0 && groupedItems != null && groupedItems.length > 0)
              groupedTransactions[groupedTransactions.length - 1].Items = groupedItems;
            groupedItems = new Array();
            groupedItems.push(newWagerItem(allTransactions[i]));
            if (i < allTransactions.length - 1) groupedTransactions[groupedTransactions.length - 1].CurrentBalance = groupedTransactions[groupedTransactions.length - 1].CurrentBalance + accumTran;
            accumTran += groupedTransactions[groupedTransactions.length - 1].TranCode == "C" ? groupedTransactions[groupedTransactions.length - 1].Amount * -1 : groupedTransactions[groupedTransactions.length - 1].Amount;


          } else {
            groupedItems.push(newWagerItem(allTransactions[i]));
          }
          holdDocumentNumber = allTransactions[i].DocumentNumber;
          holdWagerNumber = allTransactions[i].WagerNumber;
          if (i == 0) {
            groupedTransactions.push(allTransactions[i]);
            groupedTransactions[groupedTransactions.length - 1].Items = groupedItems;
            groupedTransactions[groupedTransactions.length - 1].CurrentBalance = groupedTransactions[groupedTransactions.length - 1].CurrentBalance + accumTran;
          }
        }
      }
      _reportsService.TransactionList = groupedTransactions;
    });
  };

    _reportsService.GetCustomerTransactionListByDateRange = function (customerId, initDate, finalDate,filterType) {

    var groupedItems = null;
    var holdDocumentNumber = null;
    var holdWagerNumber = null;
        return _caller.POST({ 'customerId': customerId, 'initDate': initDate, 'finalDate': finalDate, 'filterType': filterType }, 'GetTransactionsByDateRange').then(function (result) {

      var allTransactions = result;
      var groupedTransactions = new Array();
      var accumTran = 0;

      if (allTransactions != null && allTransactions.length > 0) {

        groupedTransactions = new Array();
        groupedItems = new Array();
        holdDocumentNumber = allTransactions[allTransactions.length - 1].DocumentNumber;
        holdWagerNumber = allTransactions[allTransactions.length - 1].WagerNumber;

        for (var i = allTransactions.length - 1 ; i >= 0; i--) {
          if (holdDocumentNumber != allTransactions[i].DocumentNumber || holdWagerNumber != allTransactions[i].WagerNumber) {
            groupedTransactions.push(allTransactions[i + 1]);
            if (groupedTransactions.length > 0 && groupedItems != null && groupedItems.length > 0)
              groupedTransactions[groupedTransactions.length - 1].Items = groupedItems;
            groupedItems = new Array();
            groupedItems.push(newWagerItem(allTransactions[i]));
            if (i < allTransactions.length - 1) groupedTransactions[groupedTransactions.length - 1].CurrentBalance = groupedTransactions[groupedTransactions.length - 1].CurrentBalance + accumTran;
            accumTran += groupedTransactions[groupedTransactions.length - 1].TranCode == "C" ? groupedTransactions[groupedTransactions.length - 1].Amount * -1 : groupedTransactions[groupedTransactions.length - 1].Amount;


          } else {
            groupedItems.push(newWagerItem(allTransactions[i]));
          }
          holdDocumentNumber = allTransactions[i].DocumentNumber;
          holdWagerNumber = allTransactions[i].WagerNumber;
          if (i == 0) {
            groupedTransactions.push(allTransactions[i]);
            groupedTransactions[groupedTransactions.length - 1].Items = groupedItems;
            groupedTransactions[groupedTransactions.length - 1].CurrentBalance = groupedTransactions[groupedTransactions.length - 1].CurrentBalance + accumTran;
          }
        }
      }
      _reportsService.TransactionList = groupedTransactions;
    });
  };

  _reportsService.GetCustomerTransactionListByDate = function (customerId, date) {

    var groupedItems = null;
    var holdDocumentNumber = null;
    var holdWagerNumber = null;
    return _caller.POST({ 'customerId': customerId, 'date': date }, 'GetTransactionsByDate').then(function (result) {

      var allTransactions = result;
      var groupedTransactions = new Array();

      if (allTransactions != null && allTransactions.length > 0) {

        groupedTransactions = new Array();
        groupedItems = new Array();
        holdDocumentNumber = allTransactions[0].DocumentNumber;
        holdWagerNumber = allTransactions[0].WagerNumber;

        for (var i = 0; i < allTransactions.length; i++) {
          if (holdDocumentNumber != allTransactions[i].DocumentNumber || holdWagerNumber != allTransactions[i].WagerNumber) {
            groupedTransactions.push(transaction(allTransactions[i - 1]));
            if (groupedTransactions.length > 0 && groupedItems != null && groupedItems.length > 0)
              groupedTransactions[groupedTransactions.length - 1].Items = groupedItems;
            groupedItems = new Array();
            groupedItems.push(newWagerItem(allTransactions[i]));
          } else {
            groupedItems.push(newWagerItem(allTransactions[i]));
          }
          holdDocumentNumber = allTransactions[i].DocumentNumber;
          holdWagerNumber = allTransactions[i].WagerNumber;
          if (i == allTransactions.length - 1) {
            groupedTransactions.push(transaction(allTransactions[i]));
            groupedTransactions[groupedTransactions.length - 1].Items = groupedItems;
          }
        }
      }
      _reportsService.TransactionList = groupedTransactions;
    });
  };

  _reportsService.GetDailyWagers = function (customerId, dailyFigureDate, store) {
    return _caller.POST({ 'customerId': customerId, 'dailyFigureDate': dailyFigureDate, 'store': store }, 'GetDailyWagers').then(function (result) {
      for (var i = 0; i < _reportsService.DailyFigures.ValuesPerDay.length; i++) {
        if (_reportsService.DailyFigures.ValuesPerDay[i].ThisDate == dailyFigureDate) {
          _reportsService.DailyFigures.ValuesPerDay[i].Wagers = result;

          angular.forEach(_reportsService.DailyFigures.ValuesPerDay[i].Wagers, function (wager) {
            if (wager.AmountLost != null)
              wager.AmountLost /= 100;
            if (wager.AmountWon != null)
              wager.AmountWon /= 100;
            if (wager.AcceptedDateTime != null)
              wager.AcceptedDateTime = CommonFunctions.FormatDateTime(wager.AcceptedDateTime, 1) + " " + CommonFunctions.FormatDateTime(wager.AcceptedDateTime, 2);
            if (wager.AmountWagered != null)
              wager.AmountWagered /= 100;
            if (wager.GradeDateTime != null)
              wager.GradeDateTime = CommonFunctions.FormatDateTime(wager.GradeDateTime, 1) + " " + CommonFunctions.FormatDateTime(wager.GradeDateTime, 2);
            if (wager.ToWinAmount != null)
              wager.ToWinAmount /= 100;

            angular.forEach(wager.Details, function (detail) {
              if (detail.AmountWagered != null)
                detail.AmountWagered /= 100;
              if (detail.ContestDateTime != null)
                detail.ContestDateTime = CommonFunctions.FormatDateTime(wager.ContestDateTime, 1) + " " + CommonFunctions.FormatDateTime(wager.ContestDateTime, 2);
              if (detail.GameDateTime != null)
                detail.GameDateTime = CommonFunctions.FormatDateTime(wager.GameDateTime, 1) + " " + CommonFunctions.FormatDateTime(wager.GameDateTime, 2);
              if (detail.GradeMoney != null)
                detail.GradeMoney /= 100;
              if (detail.GradeToWinAmount != null)
                detail.GradeToWinAmount /= 100;
              if (detail.ToWinAmount != null)
                detail.ToWinAmount /= 100;
            });
            wager.GradeDateTime = CommonFunctions.FormatDateTime(wager.GradeDateTime, 1);
          });
          _reportsService.DdailyFigureDate = dailyFigureDate;
          break;
        }
      }
    });
  };


  _reportsService.GetCustomerWeeklyFigures = function (customerId, goBackWeeks) {
    return _caller.POST({ 'customerId': customerId, 'goBackWeeks': goBackWeeks }, 'GetWeeklyFigures').then(function (result) {
      return result;
    });
    };

  _reportsService.GetRifHookups = function (ticketNumber, wagerNumber) {
    return _caller.POST({ 'ticketNumber': ticketNumber, 'wagerNumber': wagerNumber }, 'GetRifHookups').then(function (result) {
      return result;
    });
    };

    _reportsService.GetCustomerNonPostedCasinoPlays = function () {
        return _caller.POST({}, 'GetNonPostedCasinoPlays', null, true).then(function (result) {
            return result;
        });
    };

    _reportsService.GetCustomerNonPostedCasinoPlaysArchive = function (dailyFigureDate, systemId) {
        return _caller.POST({ dailyFigureDate, systemId }, 'GetCustomerNonPostedCasinoPlaysArchive', null, true).then(function (result) {
            return result;
        });
    };

    _reportsService.GetNonPostedCasinoPlaysArchive = function (dailyFigureDate, systemId = null) {
      return _caller.POST({ dailyFigureDate, systemId }, 'GetNonPostedCasinoPlaysArchive', null, true);
    };


  return _reportsService;

}]);
;
appModule.factory('$exportDataService', ['$http', '$q', function ($http, $q) {
    var _exportDataService = {};

  /*
    function getDataUrl(img) {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
        return canvas.toDataURL('image/jpeg');
    }
  */

    var condenseColumns = function (rows, condensedDetailColumn) {
        var newRows = [], tmpCondensedData = '', tmpRow, tmpDetails = '';
        for (var i = 0; i < rows.length; i++) {
            tmpCondensedData = {};
            tmpRow = rows[i];
            tmpDetails = '';
            for (var j = 0; j < tmpRow.length; j++) {
                // if(j != indexColumnDetail){
                var columnKey = Object.keys(tmpRow[j])[0];
                if (columnKey && columnKey != condensedDetailColumn) {
          //tmpCondensedData = { ...tmpCondensedData, ...tmpRow[j] };
          Object.assign(tmpCondensedData, tmpRow[j]);
                } else {
                    tmpDetails += tmpRow[j].Items;
                }
            }
            newRows.push([tmpCondensedData, tmpDetails]);
        }
        return newRows;
  };

    /**
       Dependencias :
            https://unpkg.com/jspdf@2.3.1/dist/jspdf.umd.js
            https://unpkg.com/jspdf-autotable@3.5.14/dist/jspdf.plugin.autotable.js
     **/
  var exportToPdf_jspdf = {
        'savePDF': function (data, configuration) {
            if (data.condensedColumn && data.header[0].length == 2 && data.condensedDetailColumn != '') {
                var tmpRows = condenseColumns(data.rows, data.condensedDetailColumn);
                data.rows = tmpRows;
            }
            let config = configuration;
            const cellTitlesColor = '#716f6f', cellContentColor = '#a3a2a2', titleColor = "#000";
            // const doc = new jspdf.jsPDF('l', 'pt');
            const doc = new jspdf.jsPDF();
            const headerCellHeight = 30;
            var posY = 14, posX = 5, singleLineHeight = 50;

            if (configuration.singleLineHeight) singleLineHeight = configuration.singleLineHeight;

            // if(configuration.logo){
            //     var imageBase64 = getDataUrl(configuration.logo),
            //         pdfLogoHeight = 15,
            //     radio = configuration.logo.height / configuration.logo.width,
            //     scale =configuration.logo.height / pdfLogoHeight;
            //     // 12 / radio =>vuelve
            //     // 20
            //     doc.addImage(imageBase64, 'jpg', posX, posY, (pdfLogoHeight / radio) ,pdfLogoHeight);
            //     posY+= pdfLogoHeight + 10;
            //     // doc.addImage(imageBase64, 'jpg', posX, posY, width = 10, height = 10, alias, compression, rotation)
            // }

            if (configuration.title) {
                doc.setTextColor(titleColor);
                if (configuration.titleFontSize) {
                    doc.setFontSize(configuration.titleFontSize);
                } else {
                    doc.setFontSize(9);
                }

                doc.text(configuration.title + '\n\n', posX, posY);
                posY += 6;
            }

            if (configuration.document_header) {
                doc.setTextColor(cellTitlesColor);
                doc.text(configuration.document_header + '\n\n', posX, posY);
                posY += 6;
            }
      let columnStyles = configuration.columnStyles ||
        { 0: { cellWidth: 30 } };

            doc.autoTable(
                {
                    startY: posY,
                    head: data.header,
                    body: data.rows,
                    rowPageBreak: 'avoid',
                    headStyles: { fillColor: [0, 0, 0] },
                    styles: {
                        minCellWidth: 60,
                        fontSize: 8,
                        overflow: 'linebreak',
                        columnWidth: 'wrap',
                    },
          columnStyles: columnStyles,

                    margin: { top: 10, right: 5, bottom: 0, left: 5 },
                    /**
                     * Se borra el contenido normal de la 1a columna,
                     * y se setea el height
                     * */
                    didParseCell: (hookData) => {
                        if (
                            hookData.section === 'body'
                        ) {
                            if (hookData.column.index === 0) {
                                var _data = hookData.cell.raw, _keys = [0];

                                if (_data) {
                                    _keys = Object.keys(_data);
                                }

                                hookData.cell.text = "";
                                hookData.cell.minCellHeight = 40;
                                hookData.row.height = (singleLineHeight * _keys.length / 2);
                            } else {
                                hookData.cell.text = "";
                                hookData.cell.styles.textColor = cellTitlesColor;
                            }
                        }
                },
                    /**
                     * 1- Se hace un custom print de las columnas marcadas como condensed
                     * lo que hace es imprimir hacia abajo Titulo / Valor, con el titulo en negrita.
                     * 2- Se setea el height en el header
                     * */
                    didDrawCell: (hookData) => {
                        if (hookData.section === 'body') {
                            var isCondensedColumn = $.isPlainObject(hookData.cell.raw);
                            // if(hookData.column.index === 0){
                            if (isCondensedColumn) {
                                // doc.setFontType("bold"); //se ocuparia cargar un font para usar esto
                                var yPos = hookData.cell.y + 4,
                                    _data = hookData.cell.raw,
                                    _keys = Object.keys(_data);

                                for (var i = 0; i < _keys.length; i++, yPos += 5) {
                                    if (data.condensedColumn) {
                                        doc.setTextColor(cellTitlesColor);
                                        doc.text(hookData.cell.x + 2, yPos, _keys[i]);
                                    }

                                    doc.setTextColor(cellContentColor); yPos += 5;

                                    /*
                                     los custom headers se envian con el  key  'customHeader'
                                     */

                                    if (_keys[i] != 'customHeader') {
                                        let _text = doc.splitTextToSize(_data[_keys[i]].replace("\n", ""), 60);
                                        doc.text(hookData.cell.x + 2, yPos, _text);
                                    } else {
                                        let _text = _data[_keys[i]].content;
                                        let _style = _data[_keys[i]].style;
                                        if (_style) {
                                            if (_style.textColor) doc.setTextColor(_style.textColor);
                                            if (_style.fontSize) doc.setFontSize(_style.fontSize);
                                            if (_style.rowHeight) hookData.row.height = _style.rowHeight;


                                        }
                                        doc.text(hookData.cell.x + 2, yPos, _text);

                                    }

                                }
                                // hookData.cell.height= (_keys.length * singleLineHeight);
                            } else {
                                hookData.cell.styles.textColor = cellContentColor;

                                if (hookData.column.index == 1) {
                                    let yPos = hookData.cell.y + 4;
                                    let _data = hookData.cell.raw;
                                    if (_data) {
                                        let _text = doc.splitTextToSize(_data.replace("\n", ""), 60);
                                        doc.text(hookData.cell.x + 2, yPos, _text);
                                    }
                                }

                            }
                        }

                        /**
                         * Se setea el height para el header
                         * */
                        if (
                            hookData.section != 'body') {
                            hookData.cell.minCellHeight = headerCellHeight;
                        }
                    }
            });

      //este codigo es si desea bajar el pdf
      //doc.save((configuration.file_name || 'document') + '.pdf');


      //este codigo es para un preview del pf
      doc.autoPrint();
      doc.output('dataurlnewwindow');


        }
    };

    /**
     Dependencias :
        window.exportFromJSON
     **/
  var exportToExcel = {
        'saveExcel': function (_data, configuration) {
      var tmpRows = _data.rows, newRows = [];
            if (_data.condensedColumn && _data.header[0].length == 2 && _data.condensedDetailColumn != '') {
                tmpRows = condenseColumns(_data.rows, _data.condensedDetailColumn);
        var data = tmpRows, tmpRow, condensedValue = '', detailsValue = '';

                for (var i = 0; i < data.length; i++) {
                    tmpRow = data[i];
                    //para la columna condensada juntamos los keys en una sola columna

                    var _values = Object.values(tmpRow[0]);
                    for (var k = 0; k < _values.length; k++) {
                        condensedValue += _values[k];
                    }

                    detailsValue = tmpRow[1];
                    newRows.push([condensedValue, detailsValue]);
                }

                newRows.unshift(_data.header[0]);
            }

            const exportType = 'xls', document_title = (configuration.file_name || 'document');
            window.exportFromJSON({ data: newRows, document_title, exportType });
        }
  };

  var exportFromCanvas = {
        'saveCanvas': function (element_id, document_title, anchor_link_id,auto_print_ticket,clonedNodeName = null,notclone = false) {
            var originalNode = document.querySelector('#' + element_id);
            var clonedNode = originalNode.cloneNode(true);
            clonedNode.id = element_id + 'Cloned';

            var oldCloned = document.getElementById(clonedNode.id);
            if (oldCloned) {
                oldCloned.remove();
            }

            document.body.appendChild(clonedNode);

            html2canvas(document.querySelector('#betSlipDivCloned')).then(canvas => {

                const doc = new jspdf.jsPDF('p', 'mm');
                var imgData = canvas.toDataURL('image/png');
                // doc.addImage(imgData, 'JPG', 10, 10,canvas.width, canvas.height);

                const imgProps = doc.getImageProperties(imgData);
                const width = doc.internal.pageSize.getWidth();
                const ratio = width / imgProps.width;
                const height = ratio * imgProps.height;

                doc.internal.pageSize.height = height; //adjust paper size according to canvas height
                doc.addImage(imgData, 'JPG', 0, 0, width / 2, height / 2);

                // doc.save(document_title + '.pdf');

                // open blob in new tab
                var blob = doc.output("blob");
                // window.open(URL.createObjectURL(blob));

                var    fileURL = URL.createObjectURL(blob);

                if(!auto_print_ticket){
                  var  anchorLink = document.getElementById(anchor_link_id);
                        anchorLink.href = fileURL;
                        anchorLink.target = '_blank';
                        // anchorLink.download = document_title;
                        anchorLink.click();
                }else{
                  //send blob to printer
                  iframe =  document.createElement('iframe'); //load content in an iframe to print later
                  document.body.appendChild(iframe);

                  iframe.style.display = 'none';
                  iframe.src = fileURL;
                  iframe.onload = function() {
                    setTimeout(function() {
                      iframe.focus();
                      iframe.contentWindow.print();
                     }, 1);
                    };
                   }

                });
       }
  };

    var exporterPDF = exportToPdf_jspdf,
        exporterExcel = exportToExcel,
        exporterCanvas = exportFromCanvas;

    _exportDataService.exportToPdf = function (data,document_title){
        exporterPDF.savePDF(data,document_title);
  };

    _exportDataService.exportToExcel = function (data,document_title){
        exporterExcel.saveExcel(data,document_title);
  };

  _exportDataService.exportFromCanvas = function (element_id, document_title, anchor_link_id,auto_print_ticket,clonedNodeName,notClone) {
    exporterCanvas.saveCanvas(element_id, document_title, anchor_link_id,auto_print_ticket,clonedNodeName,notClone);
  };

    return _exportDataService;
}]);
;
appModule.factory('$loginService', ['$http', function ($http) {

    var _caller = new ServiceCaller($http, 'Login', 'CustomerSignIn');

    return {

        //Document_Function
        RequestToken: function () {
            return _caller.POST({}, 'TemporalToken');
        },

        //Document_Function
        CustomerSignIn: function (customerId, password, obsoleteKey) {
      var cid = customerId;
      return _caller.POST({ 'customerId': cid, 'password': password, 'encryptedKey': obsoleteKey, 'agentId': null }, 'CustomerSignIn');
        },

        //Document_Function
        ObsoleteBrowserLog: function () {
            return _caller.POST({ }, 'ObsoleteBrowserLog');
        }

    };
}]);
;
appModule.factory('$customerService', ['$http', '$rootScope', '$translatorService', '$routeParams', function ($http, $rootScope, $translatorService, $routeParams) {

  var _caller = new ServiceCaller($http, 'customer');

  var _customerService = { AutoAccept: false, Restrictions: [] };

  function currentBalance(balance) {
    return {
      AvailableBalance: balance != null ? balance.AvailableBalance : null,
      CurrentBalance: balance != null ? balance.CurrentBalance : null,
      CreditLimit: balance != null ? balance.CreditLimit : null,
      CasinoBalance: balance != null ? balance.CasinoBalance : null,
      FreePlayBalance: balance != null ? balance.FreePlayBalance : null,
      PendingWagerBalance: balance != null ? balance.PendingWagerBalance : null,
      FreePlayPendingBalance: balance != null ? balance.FreePlayPendingBalance : null
    };
  };

  var _currentInfo = currentBalance(null);

  _customerService.RestrictionCodes = {
    Wagering: 'WAGERING',
    VirtualCasino: 'VCASINO',
    LiveDealer: 'LDEALER',
    Horses: 'HORSES',
    LiveBetting: 'LBETTING',
    SpecialParlayTeaserAccess: 'PTKEYRULE',
    FootballMonelyDisablePoints: 'FOOTMLDIS',
    BasketballMonelyDisablePoints: 'BASKMLDIS',
    ChangeLineInCustomerFavor: 'CSTFVRLINE',
    DebugActions: 'CSTDEBUG',
    AgentDistribution: 'AGDISTRIB',
    AgentControlCasino: 'CTRLCASINO',
    AgentPostFreePlay: 'POSTFPTRN',
    AgentHidePassword: 'HIDEPWD',
    WebRequiredPassword: 'WEBREQPASS'
  };

  _customerService.GetCustomerInfo = function (resetLastSession) {
    if (typeof resetLastSession == "undefined") resetLastSession = true;
    return _caller.POST({ resetLastSession: resetLastSession }, 'Get', null, true).then(function (result) {
      if (!result || !result.CustomerInfo) $rootScope.Logout();
      _customerService.Info = result.CustomerInfo;
      _customerService.Settings = result.CustomerSettings;
      _customerService.Balances = result.CustomerBalances;
      _customerService.Restrictions = result.CustomerRestrictions;
      _customerService.MinimumWagerAmt = result.MinimumWagerAmt;
      _customerService.Notifications = result.Notifications;
      _customerService.ViewLinesMode = result.ViewLinesMode;
      if (_customerService.Info.Active == "N") {
        UI.Notify($translatorService.Translate("Your user has been inactived. You will be logged out"), UI.Position.Top, UI.Position.Center, 200, UI.Type.Danger);
        return setTimeout(function () {
          $rootScope.Logout();
        }, 8000);
      }
      if (!$rootScope.RecentTicketProcessed)
        if (_currentInfo.CurrentBalance != null && _currentInfo != currentBalance(_customerService.Balances)) {
          if (_currentInfo.CreditLimit != result.CustomerBalances.CreditLimit)
            UI.Notify($translatorService.Translate("Credit_Limit") + ' ' + $translatorService.Translate("has_changed"), UI.Position.Top, UI.Position.Center, 200, UI.Type.Info);

          if (_currentInfo.FreePlayBalance != result.CustomerBalances.FreePlayBalance)
            UI.Notify($translatorService.Translate("FreePlay_Balance") + ' ' + $translatorService.Translate("has_changed"), UI.Position.Top, UI.Position.Center, 200, UI.Type.Info);
        }
      _currentInfo = currentBalance(_customerService.Balances);
      _customerService.Info.CurrencyCode = _customerService.Info.Currency && _customerService.Info.Currency.length > 3 ? _customerService.Info.Currency.substring(0, 3) : "";
      CommonFunctions.CustomerTimeZone = _customerService.Info.TimeZone;
      _customerService.AutoAccept = _customerService.GetCustomerRestriction('AUTOLINECH');
      $rootScope.SetPassword = _customerService.GetCustomerRestriction('WEBREQPASS');//!_customerService.Settings.WebRememberPassword;
      $rootScope.$broadcast('customerInfoLoaded');
	  if (_customerService.IsWageringDisabled()) {
		$rootScope.$broadcast('liveBettin1_restricted');
	  }

      return result;
    });
  };

  _customerService.GetCustomerInfo();

  _customerService.ForgotPassword = function (bookId) {
    return _caller.POST({ bookId }, 'ForgotPassword', null, true);
  };

  _customerService.ResetCustomerDevices = function () {
    return _caller.POST({}, 'ResetCustomerDevices', null, true);
  };

  _customerService.ResetCustomerTransUnionDevices = function () {
    return _caller.POST({}, 'ResetCustomerTransUnionDevices', null, true);
  };

  _customerService.GetCustomerTransUnionDevices = function () {
    return _caller.POST({}, 'GetCustomerTransUnionDevices', null, true);
  };

  _customerService.GetCustomerAuthorizedDevices = function () {
    return _caller.POST({}, 'GetCustomerAuthorizedDevices', null, true);
  };

  _customerService.ToogleCustomerRestrictionByCode = function (code) {
    return _caller.POST({ code }, 'ToogleCustomerRestrictionByCode', null, true);
  };

    _customerService.IsWageringDisabled = function () {
        var wageringDisabled = _customerService.GetCustomerRestriction('NWAGERSPRT');
        if (wageringDisabled) {
            return true;
        } else
            return false;
    }

  _customerService.GetCustomerRestriction = function (code) {
    for (var i = 0; _customerService.Restrictions.length > i; i++) {
      if (_customerService.Restrictions[i].Code == code) return _customerService.Restrictions[i] != null;
    }
    return null;
  };

  _customerService.GetRestriction = function (restrictionCode) {
    if (!this.Restrictions || this.Restrictions.length == 0) return null;
    var restriction = null;
    for (var i = 0; i < this.Restrictions.length; i++) {
      if (this.Restrictions[i].Code == restrictionCode) {
        if (!restriction) {
          restriction = this.Restrictions[i];
          restriction.Params = [];
        }
        restriction.Params.push({ ParamValue: this.Restrictions[i].ParamValue, ParamName: this.Restrictions[i].ParamName });
      }
    }
    return restriction;
  };

  _customerService.GetRestrictionParamValue = function (restriction, paramName) {
    if (!restriction || !paramName || !restriction.Params || restriction.Params.length == 0) return null;
    for (var i = 0; i < restriction.Params.length; i++) {
      if (restriction.Params[i].ParamName == paramName) return restriction.Params[i].ParamValue;
    }
    return null;
  };

    _customerService.GetActiveStates = function () {
        return _caller.POST({}, 'GetActiveStates', null, true);
    };

  _customerService.FlagCustomerMessage = function (messageId, targetAction) {
    _caller.POST({ 'messageId': messageId, 'targetAction': targetAction }, 'FlagMessage', null, true).success(function (response) {
      return response;
    });
  };

  _customerService.Logout = function () {
    return _caller.POST({}, 'Logout').then(function () { });
  };

  _customerService.CustomerActionLogger = function (action, data) {
    if ($rootScope.IsOffline()) return;
    return _caller.POST({ 'action': action, 'data': data || '' }, 'LogAction', null, true).then();
  };

   _customerService.GetColchianIntegration = function (customerId, password) {
    return _caller.POST({}, 'GetColchianIntegration').then();
  };

  _customerService.GetLottoURL = function () {
    return _caller.POST({}, 'GetLottoURL').then();
  };

  _customerService.GetMobitazCasinoURL = function () {
    return _caller.POST({}, 'GetMobitazCasinoURL').then();
  };

  _customerService.Sessione = function () {
    return _caller.POST({}, 'Sessione', null, true);
  };

  _customerService.IntegrationAlive = function () {
    return _caller.POST({}, 'IntegrationAlive', null, true);
  };

  _customerService.RecaptchaValidate = function (token) {
    return _caller.POST({ token: token }, 'RecaptchaValidate', null, true);
  };

  _customerService.ChangePriceType = function (priceType) {
    return _caller.POST({ priceType: priceType }, 'ChangePriceType', null, true);
  };
  
  _customerService.deleteNotification = function (params) {
    return _caller.POST(params, 'deleteNotification', null, true)
  };

  _customerService.UpdateCustomerBalance = function (balanceInfo) {
    if (balanceInfo) {
      _customerService.Balances.CurrentBalance = balanceInfo.CurrentBalance;
      _customerService.Balances.PendingWagerBalance = balanceInfo.PendingWagerBalance;
      _customerService.Balances.AvailableBalance = balanceInfo.AvailableBalance;
      _customerService.Balances.CasinoBalance = balanceInfo.NonPostedBalance;
    }
  }

  _customerService.UpdateSkinId = function(skinId){

    let _data = {'skinId':skinId};
    return _caller.POST(_data, 'UpdateSkinId', null, true).then(function (result) {
      if(result.IsSuccess){
        _customerService.SkinId = skinId;
        console.log('response updatekinId',result);
      }
        

    });
  }

  return _customerService;

}]);;
appModule.factory('$cmsService', ['$http', '$q', function ($http, $q) {

  var _caller = new ServiceCaller($http);
  var _cmsService = {};

  _pages = {};
  _cmsService.sliderImages = [];


  _cmsService.LoadPage = function (pageId, lang) {

    if (lang) lang = lang.toLowerCase();
    else lang = "";

    if (_pages[pageId]) {
      var deferred = $q.defer();
      deferred.resolve(_pages[pageId]);
      return deferred.promise;
    }

    return _caller.GET(SETTINGS.CmsSite + 'wp-json/wp/v2/pages/' + pageId + '?lang=' + lang).then(function (result) {
      _pages[pageId] = result.data;
      return result.data;
    });


  };

  _cmsService.GetSliderImages = function () {
    if (!SETTINGS.ShowSliders) return;
    return _caller.GET(SETTINGS.CmsSite + 'wp-json/wp/v2/media?_fields=source_url&order=desc').then(function (result) {
      var r = result.data;
      var arr = [];
      for (var i = 0; i < r.length; i++) {
        if (r[i].source_url && r[i].source_url.indexOf("slider") !== -1) {
          r[i].source_url += "?v=" + appVersion;
          arr.push(r[i]);
        }
      }
      if (arr.length == 1) arr.push(arr[0]);
      _cmsService.sliderImages = arr;
      return arr;
    });
  }
  return _cmsService;
}]);;
appModule.factory('$webSocketService', ['$sportsAndContestsService', '$customerService', '$errorHandler', '$rootScope', function ($sportsAndContestsService, $customerService, $errorHandler, $rootScope) {

  var _webSocketService = {
    connectionSate: 0,
    lastMessage: ""
  };
  var _connectionSate = 0;
  //var _servers = window.webConfig.webSocketServerUrl || "/ws/signalr";
  var _server = window.webConfig.webSocketServerUrl || "/ws/signalr";
  var _selectedServer;
  var _customerSubscribed = false;
  var _errorAttempts = 0;

  var sessionInfo = {
    customerid: null,
    agentId: null,
    store: null,
    sports: []
  }

  function getSelectServer () {
    return _server;
    /*if (!_servers || _servers.length == 0) return "";
    if (_selectedServer) return _servers[_selectedServer];
    else _selectedServer = Math.floor(Math.random() * _servers.length);
    return _servers[_selectedServer];*/
  };

  function logLastAction(data) {
    if (!data) return;
    _webSocketService.lastMessage = data.Context ? data.Context : data;
    var d = new Date();
    _webSocketService.lastMessage += " / " + d.toLocaleTimeString();
  }

  jQuery.support.cors = true;

  var _ws = $ != null ? $.connection : null;
  //var _server = getSelectServer();
  if (_ws && _server != "") _ws.hub.url = _server;
  var _gbsHub = _ws != null ? _ws.gbsHub : null;
  var _hubReady = null;

  function hubIsActive() {
    if (_errorAttempts > 3) {
      _webSocketService.connectionSate = 3;
      _ws.hub.stop();
      return false;
    }
    return _gbsHub;
  };

  _ws.hub.logging = false;
  _gbsHub = _ws != null ? _ws.gbsHub : null;
  if (hubIsActive() && _ws.hub) {
	_hubReady = _ws.hub.start(function () {
	}).fail(function (reason) {
	  _webSocketService.connectionSate = 2;
	  logLastAction("Connection Fail: " + reason);
	});
	_ws.hub.stateChanged(function (change) {
      if (_webSocketService.connectionSate == 2 && change.newState == 1 && sessionInfo.customerid) {
        _webSocketService.SubscribeCustomer(sessionInfo.customerid, sessionInfo.agentId, sessionInfo.store);

        for (var j = 0; j < sessionInfo.sports.length; j++) {
          _webSocketService.SubscribeSport(sessionInfo.sports[j].sportType, sessionInfo.sports[j].sportSubType, sessionInfo.store);
        }
      }
      logLastAction("Connection Changed from " + _webSocketService.connectionSate + " to " + change.newState);
	  _webSocketService.connectionSate = change.newState;
      if (change.newState != 1) _customerSubscribed = false;
	});

	window.onbeforeunload = function () {
	  _ws.hub.stop();
	  _webSocketService.connectionSate = 0;
      _customerSubscribed = false;
	};
  }
  else {
	_webSocketService.connectionSate = 2;
	logLastAction("Hub is not active");
  }

  _webSocketService.SubscribeCustomer = function (customerId, agentId, store) {
    if (!hubIsActive() || _customerSubscribed) return;
    sessionInfo.customerid = customerId;
    sessionInfo.agentId = agentId;
    sessionInfo.store = store;
    _hubReady.done(function () {
      try {
        logLastAction("SubscribeCustomer");
        _customerSubscribed = true;
        _gbsHub.server.subscribeCustomer({ CustomerId: customerId, AgentId: agentId, Store: store, Platform: $rootScope.IsMobileDevice ? 'Mobile' : 'WEB' }).fail(function (reason) {
          _errorAttempts++;
          logLastAction("SubscribeCustomer fail: " + reason);
          _customerSubscribed = false;
        });
      } catch (ex) {
        console.log(ex);
      }
    });
  };

  _webSocketService.RemoveAsiansAndRestrictedParlay = function () {
    if (!hubIsActive()) return;
    /*hubReady.done(function () {
      gbsHub.server.removeAsiansAndRestrictedParlay();
    });*/
  };

  _webSocketService.SetAsiansAndRestrictedParlay = function () {
    if (!hubIsActive()) return;
    /*hubReady.done(function () {
      gbsHub.server.setAsiansAndRestrictedParlay();
    });*/
  };

  _webSocketService.SubscribeContest = function (contestType, contestType2, store) {
    if (!hubIsActive()) return;
    _hubReady.done(function () {
      logLastAction("SubscribeContest " + contestType2);
      _gbsHub.server.subscribeSport({ ContestType: contestType, ContestType2: contestType2, Store: store, Type: 2 }).fail(function (reason) {
        _errorAttempts++;
        logLastAction("SubscribeCustomer fail: " + reason);
      });
    });
  };

  _webSocketService.SubscribeSport = function (sportType, sportSubType, store) {
    try {
      if (!hubIsActive()) return;

      var isInArray = false;
      for (var j = 0; j < sessionInfo.sports.length; j++) {
        if (sessionInfo.sports[j].sportType == sportType && sessionInfo.sports[j].sportSubType == sportSubType) {
          isInArray = true;
          break;
        }
      }
      if (!isInArray) sessionInfo.sports.push({ sportType: sportType, sportSubType: sportSubType });

      _hubReady.done(function () {
        logLastAction("SubscribeSport " + sportSubType);
        _gbsHub.server.subscribeSport({ SportType: sportType, SportSubType: sportSubType, Store: store, Type: 1 }).fail(function (reason) {
          _errorAttempts++;
          logLastAction("SubscribeCustomer fail: " + reason);
        });
      });
    } catch (ex) {
      console.log(ex);
    }
  };

  _webSocketService.SubscribeSports = function (sports) {
    if (!hubIsActive()) return;
    _hubReady.done(function () {
      logLastAction("SubscribeSports");
      sports.forEach(function (s) {
        _gbsHub.server.subscribeSport({ SportType: s.SportType, SportSubType: s.SportSubType, Store: s.Store, Type: 1 }).fail(function (reason) {
          _errorAttempts++;
          logLastAction("SubscribeSports fail: " + reason);
        });
      });
    });
  };

  _webSocketService.UnsubscribeContest = function (contestType, contestType2) {
    if (!hubIsActive()) return;
    _hubReady.done(function () {
      logLastAction("UnsubscribeContest " + contestType2);
      _gbsHub.server.unsubscribeContest({ ContestType: contestType, ContestType2: contestType2, Type: 2 }).fail(function (reason) {
        _errorAttempts++;
        logLastAction("UnsubscribeContest fail: " + reason);
      });
    });
  };

  _webSocketService.UnsubscribeSport = function (sportType, sportSubType) {
    if (!hubIsActive()) return;

    var index = -1;
    for (var i = 0; i < sessionInfo.sports.length; i++) {
      if (sessionInfo.sports[i].sportType === sportType && sessionInfo.sports[i].sportSubType === sportSubType) {
        index = i;
        break;
      }
    }
    if (index !== -1) {
      sessionInfo.sports.splice(index, 1);
    }

    _hubReady.done(function () {
      logLastAction("UnsubscribeSport " + sportSubType);
      _gbsHub.server.unsubscribeSport({ SportType: sportType, SportSubType: sportSubType, Type: 1 }).fail(function (reason) {
        _errorAttempts++;
        logLastAction("UnsubscribeSport fail: " + reason);
      });
    });
  };

  _webSocketService.UnsubscribeSports = function (sports) {
    if (!hubIsActive()) return;
    _hubReady.done(function () {
      logLastAction("UnsubscribeSports");
      sports.forEach(function (s) {
        _gbsHub.server.unsubscribeSport({ SportType: s.SportType, SportSubType: s.SportSubType, Type: 1 }).fail(function (reason) {
          _errorAttempts++;
          logLastAction("UnsubscribeSports fail: " + reason);
        });
      });
    });
  };

  _webSocketService.IsSupported = function () {
    if ("WebSocket" in window) return true;
    //_ReportError("WebSocket NOT supported by your Browser!");
    return false;
  };

  _webSocketService.IsConnected = function () {
    return _webSocketService.connectionSate != 4;
  };

  _webSocketService.GetState = function () {
    return _webSocketService.connectionSate;
  };

  if (hubIsActive()) {

    _gbsHub.client.leagueChange = function (leagues) {
      $sportsAndContestsService.LeagueChange(leagues);
    };

    _gbsHub.client.gamesChanged = function (games) {
      $sportsAndContestsService.GamesChanged(games);
    };

    _gbsHub.client.broadcastMessage = function (message) {
      message = $.parseJSON(message);
      logLastAction(message);
      switch (message.Context) {
        case "CustomerInboxChanges":
          //$inboxService.InboxChanged(message.Data);
          break;
        case "CustomerInfoChanges":
          $rootScope.$broadcast('customerInfoChanged', { resetLastSession: false });
          break;
        case "CustomerBalanceChanges":
          $customerService.CustomerBalanceChanges(message.Data);
          break;
        case "BalanceChange":
            $customerService.UpdateCustomerBalance(message.Data);
            break;
        case "LineChanges":
          $sportsAndContestsService.UpdateLines(message.Data);
          break;
        case "New Contest":
          //$sportsAndContestsService.AppendContest(message.Data);
          $rootScope.safeApply();
          break;
        case "New League":
        case "New Period":
          //$sportsAndContestsService.AppendPeriod(message.Data);
          break;
        case "New Sport":
          //$sportsAndContestsService.CreateNewSportsAndContestsRow(message.Data);
          break;
        case "Removed Contest":
          $sportsAndContestsService.RemoveContest(message.Data);
          break;
        case "Removed League":
          //$sportsAndContestsService.RemoveLeague(message.Data);
          break;
        case "Removed Period":
          //$sportsAndContestsService.RemovePeriod(message.Data);
          break;
        case "Removed Sport":
          //$sportsAndContestsService.RemoveSportsAndContestsRow(message.Data);
          break;
        case "Request User Subscribtion":
          _webSocketService.SubscribeCustomer($customerService.Info.CustomerID.trim(), $customerService.Info.Store.trim());
          break;
      }
    };

    _gbsHub.client.closeSession = function () {
      $rootScope.Logout();
    };
  }

  _webSocketService.GetCurrentServer = function () {
    return _server;
  };

  $rootScope.$on("customerInfoLoaded", function () {
    if (!$customerService.Info || !$customerService.Info.CustomerID || $customerService.Info.IsDemo) {
      if ($customerService.Info.IsDemo) _ws.hub.stop();
      return;
    }
    _webSocketService.SubscribeCustomer($customerService.Info.CustomerID.trim(), $customerService.Info.AgentID.trim(), $customerService.Info.Store.trim());
  });

  return _webSocketService;

}]);;
appModule.factory('$signupService', ['$http', function ($http) {

  var _caller = new ServiceCaller($http, 'signup');
  var _signupService = {};

  _signupService.CreateMyAccount = function (customerSignInfo) {

    customerSignInfo.bookId = SETTINGS.BookId;
    customerSignInfo.agentId = SETTINGS.SignUpAgentId;
    return _caller.POST(customerSignInfo, 'CreateMyAccount').then();
  };

  _signupService.CreateMyAccountExternal = function (customerSignInfo) {
    customerSignInfo.bookId = SETTINGS.BookId;
    customerSignInfo.agentId = SETTINGS.SignUpAgentId;
    return _caller.POST(customerSignInfo, 'CreateMyAccountExternal').then();
  };

  return _signupService;

}]);
;
