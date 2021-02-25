function openWindow(url, width, height) {
	var callback = function() {
		window.location.reload(true);
	};
	if (window.microsoftTeams) {
		microsoftTeams.initialize();
		microsoftTeams.authentication.authenticate({
			url: url,
			width: width,
			height: height,
			successCallback: callback,
			failureCallback: callback,
		});
  }
  else {
		window.open(url, "_blank", "width=" + width + ", height=" + height);
	}
}

function signInWithAzure(event, source) {
	event.preventDefault();
	openWindow("/auth/login_azure?aadObjectId="+encodeURIComponent(userData.aadObjectId)+"&existingUser="+userData.existingUser+"&source="+source, 500, 650);
}


/**
 * To make a post request to tab pages
 */
function postData(url, user){
	method = "post";
	var form = document.createElement("form");
	form.setAttribute("method", method);
	form.setAttribute("action", url);

	var hiddenField = document.createElement("input");
	hiddenField.setAttribute("type", "hidden");
	hiddenField.setAttribute("name", "user");
	hiddenField.setAttribute("value", JSON.stringify(user));
	form.appendChild(hiddenField);

	document.body.appendChild(form);
	form.submit();
}

/**
  * Signout of Tab
*/
function signoutTab(source){
	postData("/signout?source="+source, userData);
}

if (window != window.top) {
    microsoftTeams.initialize();
    microsoftTeams.getContext(function (context) {
        TeamsTheme.fix(context);
    });
}

let config = {
	clientId: "",
	redirectUri: window.location.origin + "/silent-end",
	cacheLocation: "localStorage",
	navigateToLoginRequestUrl: false,
};

// Loads data for the given user
function loadData(upn) {
	if (upn) {
		config.extraQueryParameters = "scope=openid+profile&login_hint=" + encodeURIComponent(upn);
    }
    else {
		config.extraQueryParameters = "scope=openid+profile";
	}
	let authContext = new AuthenticationContext(config);
	// See if there's a cached user and it matches the expected user
	let user = authContext.getCachedUser();
	if (user) {
		if (user.userName !== upn) {
			authContext.clearCache();
		}
	}
	// Get the id token (which is the access token for resource = clientId)
	let token = authContext.getCachedToken(config.clientId);
	if (token) {
		showProfileInformation(token);
    } 
    else {
		// No token, or token is expired
		authContext._renewIdToken(function(err, idToken) {
			if (err) {
				console.log("Renewal failed: " + err);
				login();
            } 
            else {
				showProfileInformation(idToken);
			}
		});
	}
}
// Login to Azure AD
function login(forceReload) {
	$("#divError").text("").css({
		display: "none"
	});
	$("#divProfile").css({
		display: "none"
	});
	$("#btnLogin").css({
		display: "none"
	});
	microsoftTeams.authentication.authenticate({
		url: window.location.origin + "/auth/login_azure",
		width: 600,
		height: 535,
		successCallback: function(result) {
			// AuthenticationContext is a singleton
			let authContext = new AuthenticationContext(config);
			let idToken = authContext.getCachedToken(config.clientId);
			if (idToken) {
				showProfileInformation(idToken);
            } 
            else {
				console.error("Error getting cached id token. This should never happen.");
				// At this point we have to get the user involved, so show the login button
				if(forceReload) {
					window.location.reload(true);
				} else {
					$("#btnLogin").css({
						display: "block"
					});
				}
			};
		},
		failureCallback: function(reason) {
			console.log("Login failed: " + reason);
			if (reason === "CancelledByUser" || reason === "FailedToOpenWindow") {
				console.log("Login was blocked by popup blocker or canceled by user.");
			}
			// At this point we have to get the user involved, so show the login button
			$("#btnLogin").css({
				display: "block"
			});
			$("#divError").text(reason).css({
				display: ""
			});
			$("#divProfile").css({
				display: "none"
			});
			$('.loading-block').hide();
		}
	});
}
// Get the user's profile information from the id token
function showProfileInformation(idToken) {
	$.ajax({
		url: window.location.origin + "/api/validateToken",
		beforeSend: function(request) {
			request.setRequestHeader("Authorization", "Bearer " + idToken);
		},
		success: function(user) {
			pulsarnewslogin(user);
		},
		error: function(xhr, textStatus, errorThrown) {
			console.log("textStatus: " + textStatus + ", errorThrown:" + errorThrown);
			$("#divError").text(errorThrown).css({
				display: ""
			});
			$("#divProfile").css({
				display: "none"
			});
		},
	});
}
/**
 * Display message if there are no pull requests/issues for that repo
 */
function displayNoRecordsMessage(pageType) {
	var div = document.getElementById('settingContainer');
	div.innerHTML = '';
	if (pageType == 'cards') $('#noCardsContainer').show();
	else if (pageType == 'calender') {
		$('#noCardsCalenderContainer').show();
    } 
    else if (pageType == 'recentboards') {
		$('#noRecentBoardsContainer').show();
    } 
    else if (pageType == 'noboardsaccess') {
		$('#noAccessToBoards').show();
	} else $('#noBoardsErrorContainer').show();
}
/**
 * Display generic message if incorrect parms passed
 */
function displayErrorMessage() {
	var div = document.getElementById('settingContainer');
	div.innerHTML = '';
	$('#genericErrorContainer').show();
}
// Navigating to specific Tab
function navigateToTab(data) {
	try {
		const tab = list.find(item => item.internalTabInstanceId === data.item.internalTabInstanceId);
		microsoftTeams.navigateToTab(tab);
	} catch (e) {
		console.log(e);
		displayErrorMessage();
	}
}

//Filter html and script tags
function HtmlEncode(text) {
	var plainText = text.replace(/</g, "&lt;").replace(/>/g, "&gt;");
	return plainText;
}