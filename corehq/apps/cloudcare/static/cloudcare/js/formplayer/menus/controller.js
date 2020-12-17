/*global Backbone */

hqDefine("cloudcare/js/formplayer/menus/controller", function () {
    var FormplayerFrontend = hqImport("cloudcare/js/formplayer/app"),
        Util = hqImport("cloudcare/js/formplayer/utils/util");
    var selectMenu = function (options) {

        options.preview = FormplayerFrontend.currentUser.displayOptions.singleAppMode;

        var fetchingNextMenu = FormplayerFrontend.getChannel().request("app:select:menus", options);

        /*
         Determine the next screen to display.  Could be
         a list of commands (modules and/or forms)
         a list of entities (cases) and their details
         */
        $.when(fetchingNextMenu).done(function (menuResponse) {

            //set title of tab to application name
            if (menuResponse.breadcrumbs) {
                document.title = menuResponse.breadcrumbs[0];
            }

            // show any notifications from Formplayer
            if (menuResponse.notification && !_.isNull(menuResponse.notification.message)) {
                FormplayerFrontend.getChannel().request("handleNotification", menuResponse.notification);
            }

            // If redirect was set, clear and go home.
            if (menuResponse.clearSession) {
                FormplayerFrontend.trigger("apps:currentApp");
                return;
            }

            if (menuResponse.autolaunch) {
                FormplayerFrontend.trigger("menu:select", menuResponse.autolaunch);
                return;
            }

            var urlObject = Util.currentUrlToObject();

            // If we don't have an appId in the URL (usually due to form preview)
            // then parse the appId from the response.
            if (urlObject.appId === undefined || urlObject.appId === null) {
                if (menuResponse.appId === null || menuResponse.appId === undefined) {
                    FormplayerFrontend.trigger('showError', "Response did not contain appId even though it was" +
                        "required. If this persists, please report an issue to CommCareHQ");
                    FormplayerFrontend.trigger("apps:list");
                    return;
                }
                urlObject.appId = menuResponse.appId;
                Util.setUrlToObject(urlObject);
            }

            showMenu(menuResponse);
            // If a search exists in urlObject, make set search bar continues to show search
            if (urlObject.search !== null) {
                $('#searchText').val(urlObject.search);
            }

            if (menuResponse.shouldRequestLocation) {
                hqImport("cloudcare/js/formplayer/menus/util").handleLocationRequest(options);
            }
            hqImport("cloudcare/js/formplayer/menus/util").startOrStopLocationWatching(menuResponse.shouldWatchLocation);
        }).fail(function () {
            //  if it didn't go through, then it displayed an error message.
            // the right thing to do is then to just stay in the same place.
        });
    };

    var selectDetail = function (caseId, detailIndex, isPersistent) {
        var urlObject = Util.currentUrlToObject();
        if (!isPersistent) {
            urlObject.addStep(caseId);
        }
        var fetchingDetails = FormplayerFrontend.getChannel().request("entity:get:details", urlObject, isPersistent);
        $.when(fetchingDetails).done(function (detailResponse) {
            showDetail(detailResponse, detailIndex, caseId);
        }).fail(function () {
            FormplayerFrontend.trigger('navigateHome');
        });
    };

    var showMenu = function (menuResponse) {
        var menuListView = hqImport("cloudcare/js/formplayer/menus/util").getMenuView(menuResponse);
        var appPreview = FormplayerFrontend.currentUser.displayOptions.singleAppMode;
        var changeFormLanguage = FormplayerFrontend.currentUser.changeFormLanguage;

        if (menuListView) {
            FormplayerFrontend.regions.getRegion('main').show(menuListView);
        }
        if (menuResponse.persistentCaseTile && !appPreview) {
            showPersistentCaseTile(menuResponse.persistentCaseTile);
        } else {
            FormplayerFrontend.regions.getRegion('persistentCaseTile').empty();
        }

        if (menuResponse.breadcrumbs) {
            hqImport("cloudcare/js/formplayer/menus/util").showBreadcrumbs(menuResponse.breadcrumbs);
            if (menuResponse.langs && menuResponse.langs.length > 1 && !appPreview && changeFormLanguage) {
                hqImport("cloudcare/js/formplayer/menus/util").showLanguageMenu(menuResponse.langs);
            }
        } else {
            FormplayerFrontend.regions.getRegion('breadcrumb').empty();
        }
        if (menuResponse.appVersion) {
            FormplayerFrontend.trigger('setVersionInfo', menuResponse.appVersion);
        }
    };

    var showPersistentCaseTile = function (persistentCaseTile) {
        var detailView = getCaseTile(persistentCaseTile);
        FormplayerFrontend.regions.getRegion('persistentCaseTile').show(detailView.render());
    };

    var showDetail = function (model, detailTabIndex, caseId) {
        var detailObjects = model.models;
        // If we have no details, just select the entity
        if (detailObjects === null || detailObjects === undefined || detailObjects.length === 0) {
            FormplayerFrontend.trigger("menu:select", caseId);
            return;
        }
        var detailObject = detailObjects[detailTabIndex];
        var menuListView = getDetailList(detailObject);

        var tabModels = _.map(detailObjects, function (detail, index) {
            return {title: detail.get('title'), id: index, active: index === detailTabIndex};
        });
        var tabCollection = new Backbone.Collection();
        tabCollection.reset(tabModels);

        var tabListView = hqImport("cloudcare/js/formplayer/menus/views").DetailTabListView({
            collection: tabCollection,
            showDetail: function (detailTabIndex) {
                showDetail(model, detailTabIndex, caseId);
            },
        });

        $('#select-case').off('click').click(function () {
            if (hqImport('hqwebapp/js/toggles').toggleEnabled('APP_ANALYTICS')) {
                hqImport('analytix/js/kissmetrix').track.event('Case claim', {
                    domain: FormplayerFrontend.getChannel().request('currentUser').domain,
                    name: model.models[0].attributes.details[0], // extracting case list name from model object
                });
            }
            FormplayerFrontend.trigger("menu:select", caseId);
        });
        $('#case-detail-modal').find('.js-detail-tabs').html(tabListView.render().el);
        $('#case-detail-modal').find('.js-detail-content').html(menuListView.render().el);
        $('#case-detail-modal').modal('show');

        if (model.isPersistentDetail) {
            $('#case-detail-modal').find('#select-case').hide();
        } else {
            $('#case-detail-modal').find('#select-case').show();
        }
    };

    var getDetailList = function (detailObject) {
        var i;
        if (detailObject.get('entities')) {
            var entities = detailObject.get('entities');
            var listModel = [];
            // we need to map the details and headers JSON to a list for a Backbone Collection
            for (i = 0; i < entities.length; i++) {
                var listObj = {};
                listObj.data = entities[i].data;
                listObj.id = i;
                listModel.push(listObj);
            }
            var listCollection = new Backbone.Collection();
            listCollection.reset(listModel);
            var menuData = {
                collection: listCollection,
                headers: detailObject.get('headers'),
                styles: detailObject.get('styles'),
                title: detailObject.get('title'),
            };
            return hqImport("cloudcare/js/formplayer/menus/views").CaseListDetailView(menuData);
        }

        var headers = detailObject.get('headers');
        var details = detailObject.get('details');
        var styles = detailObject.get('styles');
        var detailModel = [];
        // we need to map the details and headers JSON to a list for a Backbone Collection
        for (i = 0; i < headers.length; i++) {
            var obj = {};
            obj.data = details[i];
            obj.header = headers[i];
            obj.style = styles[i];
            obj.id = i;
            detailModel.push(obj);
        }
        var detailCollection = new Backbone.Collection();
        detailCollection.reset(detailModel);
        return hqImport("cloudcare/js/formplayer/menus/views").DetailListView({
            collection: detailCollection,
        });
    };

    // return a case tile from a detail object (for persistent case tile)
    var getCaseTile = function (detailObject) {
        var detailModel = new Backbone.Model({
            data: detailObject.details,
            id: 0,
        });
        var numEntitiesPerRow = detailObject.numEntitiesPerRow || 1;
        var numRows = detailObject.maxHeight;
        var numColumns = detailObject.maxWidth;
        var useUniformUnits = detailObject.useUniformUnits || false;
        var caseTileStyles = hqImport("cloudcare/js/formplayer/menus/views").buildCaseTileStyles(detailObject.tiles, numRows, numColumns,
            numEntitiesPerRow, useUniformUnits, 'persistent');
        // Style the positioning of the elements within a tile (IE element 1 at grid position 1 / 2 / 4 / 3
        $("#persistent-cell-layout-style").html(caseTileStyles[0]).data("css-polyfilled", false);
        // Style the grid (IE each tile has 6 rows, 12 columns)
        $("#persistent-cell-grid-style").html(caseTileStyles[1]).data("css-polyfilled", false);
        return hqImport("cloudcare/js/formplayer/menus/views").PersistentCaseTileView({
            model: detailModel,
            styles: detailObject.styles,
            tiles: detailObject.tiles,
            maxWidth: detailObject.maxWidth,
            maxHeight: detailObject.maxHeight,
            prefix: 'persistent',
            hasInlineTile: detailObject.hasInlineTile,
        });
    };

    return {
        selectDetail: selectDetail,
        selectMenu: selectMenu,
        showMenu: showMenu,
    };
});
