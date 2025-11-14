/*!
 * ASP.NET SignalR JavaScript Library v2.3.0-rtm
 * http://signalr.net/
 *
 * Copyright (c) .NET Foundation. All rights reserved.
 * Licensed under the Apache License, Version 2.0. See License.txt in the project root for license information.
 *
 */

/// <reference path="..\..\SignalR.Client.JS\Scripts\jquery-1.6.4.js" />
/// <reference path="jquery.signalR.js" />
(function ($, window, undefined) {
    /// <param name="$" type="jQuery" />
    "use strict";

    if (typeof ($.signalR) !== "function") {
        throw new Error("SignalR: SignalR is not loaded. Please ensure jquery.signalR-x.js is referenced before ~/signalr/js.");
    }

    var signalR = $.signalR;

    function makeProxyCallback(hub, callback) {
        return function () {
            // Call the client hub method
            callback.apply(hub, $.makeArray(arguments));
        };
    }

    function registerHubProxies(instance, shouldSubscribe) {
        var key, hub, memberKey, memberValue, subscriptionMethod;

        for (key in instance) {
            if (instance.hasOwnProperty(key)) {
                hub = instance[key];

                if (!(hub.hubName)) {
                    // Not a client hub
                    continue;
                }

                if (shouldSubscribe) {
                    // We want to subscribe to the hub events
                    subscriptionMethod = hub.on;
                } else {
                    // We want to unsubscribe from the hub events
                    subscriptionMethod = hub.off;
                }

                // Loop through all members on the hub and find client hub functions to subscribe/unsubscribe
                for (memberKey in hub.client) {
                    if (hub.client.hasOwnProperty(memberKey)) {
                        memberValue = hub.client[memberKey];

                        if (!$.isFunction(memberValue)) {
                            // Not a client hub function
                            continue;
                        }

                        // Use the actual user-provided callback as the "identity" value for the registration.
                        subscriptionMethod.call(hub, memberKey, makeProxyCallback(hub, memberValue), memberValue);
                    }
                }
            }
        }
    }

    $.hubConnection.prototype.createHubProxies = function () {
        var proxies = {};
        this.starting(function () {
            // Register the hub proxies as subscribed
            // (instance, shouldSubscribe)
            registerHubProxies(proxies, true);

            this._registerSubscribedHubs();
        }).disconnected(function () {
            // Unsubscribe all hub proxies when we "disconnect".  This is to ensure that we do not re-add functional call backs.
            // (instance, shouldSubscribe)
            registerHubProxies(proxies, false);
        });

        proxies['gbsHub'] = this.createHubProxy('gbsHub'); 
        proxies['gbsHub'].client = { };
        proxies['gbsHub'].server = {
            closeCustomerSession: function (customerId) {
                return proxies['gbsHub'].invoke.apply(proxies['gbsHub'], $.merge(["CloseCustomerSession"], $.makeArray(arguments)));
             },

            disconnectUser: function () {
                return proxies['gbsHub'].invoke.apply(proxies['gbsHub'], $.merge(["DisconnectUser"], $.makeArray(arguments)));
             },

            getGame: function (gameNum) {
                return proxies['gbsHub'].invoke.apply(proxies['gbsHub'], $.merge(["GetGame"], $.makeArray(arguments)));
             },

            getGameLines: function (gameNum, periodNumber, store) {
                return proxies['gbsHub'].invoke.apply(proxies['gbsHub'], $.merge(["GetGameLines"], $.makeArray(arguments)));
             },

            subscribeAdminUser: function () {
                return proxies['gbsHub'].invoke.apply(proxies['gbsHub'], $.merge(["SubscribeAdminUser"], $.makeArray(arguments)));
             },

            subscribeContest: function (subscription) {
                return proxies['gbsHub'].invoke.apply(proxies['gbsHub'], $.merge(["SubscribeContest"], $.makeArray(arguments)));
             },

            subscribeCustomer: function (user) {
                return proxies['gbsHub'].invoke.apply(proxies['gbsHub'], $.merge(["SubscribeCustomer"], $.makeArray(arguments)));
             },

            subscribeSport: function (subscription) {
                return proxies['gbsHub'].invoke.apply(proxies['gbsHub'], $.merge(["SubscribeSport"], $.makeArray(arguments)));
             },

            subscribeSports: function (subscriptionList) {
                return proxies['gbsHub'].invoke.apply(proxies['gbsHub'], $.merge(["SubscribeSports"], $.makeArray(arguments)));
             },

            syncGameLines: function (gameNum, periodNumber, store) {
                return proxies['gbsHub'].invoke.apply(proxies['gbsHub'], $.merge(["SyncGameLines"], $.makeArray(arguments)));
             },

            unsubscribeContest: function (subscription) {
                return proxies['gbsHub'].invoke.apply(proxies['gbsHub'], $.merge(["UnsubscribeContest"], $.makeArray(arguments)));
             },

            unsubscribeSport: function (subscription) {
                return proxies['gbsHub'].invoke.apply(proxies['gbsHub'], $.merge(["UnsubscribeSport"], $.makeArray(arguments)));
             },

            unsubscribeSports: function (subscriptionList) {
                return proxies['gbsHub'].invoke.apply(proxies['gbsHub'], $.merge(["UnsubscribeSports"], $.makeArray(arguments)));
             }
        };

        return proxies;
    };

    signalR.hub = $.hubConnection("/signalr", { useDefaultPath: false });
    $.extend(signalR, signalR.hub.createHubProxies());

}(window.jQuery, window));
