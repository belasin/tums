// import Nevow.Athena
firewall.PS = Nevow.Athena.Widget.subclass('firewall.PS');
firewall.PS.methods(
    function nodeInserted(self) {
        self.initFirewallRulesInterface();
        self.checkSecurity();
        self.callRemote('parseFirewallResult');
        //Initialise the firewall rules form
        self.initFirewallRulesForm();

        self.initFirewallForwardForm();

        self.initFirewallRedirectForm();

        self.initFirewallMasqForm();
        
        self.initFirewallSNATForm();

        self.initFirewallPolicyForm();

        self.initFirewallQosForm();

        self.initFirewallZoneForm();

        //Attach the firewall test and apply events
        $('testFirewall').addEvent('click', function() {
            self.callRemote('testRules');
        });
        
        $('applyFirewall').addEvent('click', function() {
            self.callRemote('applyRules');
        });

    },

    function initFirewallRulesForm(self) {
        //Get the firewall Rule adding and Editing form going
        self.attachDialogEvents('firewallRulesFormDialog', false);
        $('fwAddRuleButton').addEvent('click', function(e) {
            self.prepareRulesForm($('fwAddRuleButton'), null);
        });
        //Define the validation information for the form
        rulesFormValidators = new Hash();
        rulesFormValidators["sip"] = self.validateIPorCIDR;
        rulesFormValidators["sport"] = self.validatePortRange;
        rulesFormValidators["dip"] = self.validateIPorCIDR;
        rulesFormValidators["dport"] = self.validatePortRange;
        //Initialise the form events and the validation handeling
        self.hookForm(  'firewallRulesForm', 
                        'submitFirewallRule', 
                        rulesFormValidators,
                        "firewallRulesFormDialog");
        connect('firewallRulesForm-sport', 'onkeyup', function(){
            var dport = getElement('firewallRulesForm-dport-field').childNodes[2];
            var dportin = getElement('firewallRulesForm-dport');
            var origText = "Destination port OR other protocol subtype (Blank for any)";
            if (getElement('firewallRulesForm-sport').value == ""){
                dportin.disabled = false;
                dport.innerHTML = origText;
            }
            else {
                dportin.disabled = true;
                dportin.value = "";
                dport.innerHTML = "<strong>Disabled</strong>. You may not specify both a source and destination port at the same time. Since source ports are usualy random for a known destination, your attempted rule will make no sense";
            }
        });

        $('firewallRulesForm-dport').addEvent('keyup', function(){
            var sport = getElement('firewallRulesForm-sport-field').childNodes[2];
            var sportin = getElement('firewallRulesForm-sport');
            var origText = "Source port (Blank for Any)";
            if (getElement('firewallRulesForm-dport').value == ""){
                sportin.disabled = false;
                sport.innerHTML = origText;
            }
            else {
                sportin.disabled = true;
                sportin.value = "";
                sport.innerHTML = "<strong>Disabled</strong>. You may not specify both a source and destination port at the same time. Since source ports are usualy random for a known destination port, your attempted rule will would make no sense.";
            }
        });

        //Define that Source IP's must not have an all option in the dropdown box for szone
        $('firewallRulesForm-sip').addEvent('keyup', function() {
            var szone = getElement('firewallRulesForm-szone');
            if(getElement('firewallRulesForm-sip').value != "") {
                //Disable the 'all' option for szone
                for (i=0;i<szone.length;i++)
                {
                    if(szone.options[i].value == 'all') {
                        szone.options[i].disabled = true;
                        if(szone.options[i].selected) {
                            szone.selectedIndex = 0;
                        }
                    }
                }
            } else {
                for (i=0;i<szone.length;i++)
                {
                    if(szone.options[i].value == 'all') {
                        szone.options[i].disabled = false;
                    }
                }
            }
        });

        //Define that Dest IP's must not have an all option in the dropdown box for dzone
        $('firewallRulesForm-dip').addEvent('keyup', function() {
            var dzone = getElement('firewallRulesForm-dzone');
            if(getElement('firewallRulesForm-dip').value != "") {
                //Disable the 'all' option for dzone
                for (i=0;i<dzone.length;i++)
                {
                    if(dzone.options[i].value == 'all') {
                        dzone.options[i].disabled = true;
                        if(dzone.options[i].selected) {
                            dzone.selectedIndex = 0;
                        }
                    }
                }
            } else {
                for (i=0;i<dzone.length;i++)
                {
                    if(dzone.options[i].value == 'all') {
                        dzone.options[i].disabled = false;
                    }
                }
            }
        });
    },

    function initFirewallRulesInterface(self) {
        //Make List sortable
        $('firewallRules')["sortable"] = new Sortables($('firewallRules'), {
                constrain: false,
                clone: true,
                opacity: 0.4,
                handle: ".move",
                revert: {
                    duration: 150
                },

                onComplete: function(el) {
                    var sort_order = new Array();
                    var count = 0
                    $$('.dynRow').each(function(element) {
                        sort_order[count] = element.id;
                        count++;
                    });
                    self.setListAlternateClass("firewallRules");
                    self.callRemote('applyFirewallRuleOrder', sort_order);
                }

        });
        //Bind Edit
        $$('#firewallRules td.edit').each(function(el) {
            if(!el["hasEditEvent"]) {
                el.addEvent("click", function(e) {
                    new Event(e).stop(); //Stop the usual form processing
                    var parent = el.getParent('li');
                    self.prepareRulesForm(parent, parent.id);
                });
            }
            el["hasEditEvent"] = true;
        });
        //Bind Delete
        self.attachDelete("firewallRules", "delFirewallRule", "fwrule");
    },

    function prepareRulesForm(self, clickElement, ruleID) {
        $('firewallRulesFormTitle').innerHTML = ruleID == null ? "New Rule" : "Edit Rule";
        //Should perhaps add a loading dialog here
        self.callRemote('getRuleFormData', ruleID).addCallback(function(data) {
            //Should hide the loading dialog here
            self.populateForm('firewallRulesForm', data, ruleID);
            self.showDialogBox("firewallRulesFormDialog", clickElement);
        });
    },
    
    function checkEmpty(self, listName) {
        if($$('#'+listName+' td').length < 1) {
            if($$('#'+listName+' tr.empty').length < 1) {
                var element = new Element('tr', {
                    'class': 'empty',
                    'html': 'No Entries'
                });
                $(listName).adopt(element);
            }
        } else {
            $$('#'+listName+' tr.empty').each(function(el) {
                el.dispose();
            });
        }
    },

    function initListEvents(self, listName, deleteHook, prepFormEditHook, prefix) {
        self.checkEmpty(listName);
        //Bind Edit
        $$('#'+listName+' td.edit').each(function(el) {
            if(!el["hasEditEvent"]) {
                el.addEvent("click", function(e) {
                    new Event(e).stop(); //Stop the usual form processing
                    var parent = el.getParent('tr');
                    prepFormEditHook(parent, parent.id);
                });
            }
            el["hasEditEvent"] = true;
        });
        //Bind Delete
        self.attachDelete(listName, deleteHook, prefix);

    },

    /// Port forwarding

    function initForwardListEvents(self) {
        self.initListEvents("firewallForwardRules", "delForwardPort", function(clickElement, ruleID) {self.prepareForwardForm(clickElement, ruleID);}, "forwardRule");
    },
    
    function initFirewallForwardForm(self) {
        self.attachDialogEvents('firewallFwdRulesFormDialog', false);
        $('fwAddFwdRuleButton').addEvent('click', function(e) {
            self.prepareForwardForm($('fwAddFwdRuleButton'), null);
        });
        //Define the validation information for the form
        forwardFormValidators = new Hash();
        forwardFormValidators["sip"] = self.validateIPorCIDR;
        forwardFormValidators["port"] = self.validatePortRange;
        forwardFormValidators["fwdip"] = self.validateIP;
        forwardFormValidators["extip"] = self.validateIP;
        forwardFormValidators["dport"] = self.validatePort;
        //Initialise the form events and the validation handeling
        self.hookForm(  'firewallForwardPortForm', 
                        'submitForwardPort', 
                        forwardFormValidators,
                        "firewallFwdRulesFormDialog");
        self.initForwardListEvents();

    },
    
    function prepareForwardForm(self, clickElement, ruleID) {
        $('firewallFwdRulesFormTitle').innerHTML = ruleID == null ? "New Port Forward" : "Edit Port Forward";
        //Should perhaps add a loading dialog here
        self.callRemote('getForwardFormData', ruleID).addCallback(function(data) {
            //Should hide the loading dialog here
            self.populateForm('firewallForwardPortForm', data, ruleID);
            self.showDialogBox("firewallFwdRulesFormDialog", clickElement);
        });
    },

    ///End of portforwarding

    ///Redirection / Transparent Proxy

    function initRedirectListEvents(self) {
        self.initListEvents("firewallRedirectRules", "delRedirectRule", function(clickElement, ruleID) {self.prepareRedirectForm(clickElement, ruleID);}, "redirectRule");
    },
    
    function initFirewallRedirectForm(self) {
        self.attachDialogEvents('firewallRedirectRulesFormDialog', false);
        $('fwAddRedirectRuleButton').addEvent('click', function(e) {
            self.prepareRedirectForm($('fwAddRedirectRuleButton'), null);
        });
        //Define the validation information for the form
        redirectFormValidators = new Hash();
        redirectFormValidators["srcnet"] = self.validateIPorCIDR;
        redirectFormValidators["dstport"] = self.validatePort;
        redirectFormValidators["srcport"] = self.validatePort;
        redirectFormValidators["dstnet"] = self.validateIPorCIDR;
        //Initialise the form events and the validation handeling
        self.hookForm(  'firewallRedirectForm', 
                        'submitRedirectRule', 
                        redirectFormValidators,
                        "firewallRedirectRulesFormDialog");
        self.initRedirectListEvents();

    },
    
    function prepareRedirectForm(self, clickElement, ruleID) {
        $('firewallRedirectRulesFormTitle').innerHTML = ruleID == null ? "New Redirect Rule" : "Edit Redirect Rule";
        //Should perhaps add a loading dialog here
        self.callRemote('getRedirectFormData', ruleID).addCallback(function(data) {
            //Should hide the loading dialog here
            self.populateForm('firewallRedirectForm', data, ruleID);
            self.showDialogBox("firewallRedirectRulesFormDialog", clickElement);
        });
    },

    ///End of portforwarding

    ///NAT / Masquarading

    function initMasqListEvents(self) {
        self.initListEvents("firewallMasqRules", "delMasqRule", function(clickElement, ruleID) {self.prepareMasqForm(clickElement, ruleID);}, "masqRule");
    },
    
    function initFirewallMasqForm(self) {
        self.attachDialogEvents('firewallMasqRulesFormDialog', false);
        $('fwAddMasqRuleButton').addEvent('click', function(e) {
            self.prepareMasqForm($('fwAddMasqRuleButton'), null);
        });
        //Define the validation information for the form
        masqFormValidators = new Hash();
        masqFormValidators["srcnet"] = self.validateIPorCIDR;
        masqFormValidators["natip"] = self.validateIP;
        masqFormValidators["dstnet"] = self.validateIPorCIDR;
        masqFormValidators["port"] = self.validatePort;
        //Initialise the form events and the validation handeling
        self.hookForm(  'firewallMasqForm', 
                        'submitMasqRule', 
                        masqFormValidators,
                        "firewallMasqRulesFormDialog");
        self.initMasqListEvents();

    },
    
    function prepareMasqForm(self, clickElement, ruleID) {
        $('firewallMasqRulesFormTitle').innerHTML = ruleID == null ? "New Nat Rule" : "Edit Nat Rule";
        //Should perhaps add a loading dialog here
        self.callRemote('getMasqFormData', ruleID).addCallback(function(data) {
            //Should hide the loading dialog here
            self.populateForm('firewallMasqForm', data, ruleID);
            self.showDialogBox("firewallMasqRulesFormDialog", clickElement);
        });
    },

    ///End of NAT / Masq
    
    ///SNAT / Source NAT

    function initSNATListEvents(self) {
        self.initListEvents("firewallSNATRules", "delSNATRule", function(clickElement, ruleID) {self.prepareSNATForm(clickElement, ruleID);}, "snatRule");
    },
    
    function initFirewallSNATForm(self) {
        self.attachDialogEvents('firewallSNATRulesFormDialog', false);
        $('fwAddSNATRuleButton').addEvent('click', function(e) {
            self.prepareSNATForm($('fwAddSNATRuleButton'), null);
        });
        //Define the validation information for the form
        snatFormValidators = new Hash();
        snatFormValidators["dstip"] = self.validateIPorCIDR;
        snatFormValidators["srcip"] = self.validateIP;
        //Initialise the form events and the validation handeling
        self.hookForm(  'firewallSNATForm', 
                        'submitSNATRule', 
                        snatFormValidators,
                        "firewallSNATRulesFormDialog");
        self.initSNATListEvents();

    },
    
    function prepareSNATForm(self, clickElement, ruleID) {
        $('firewallSNATRulesFormTitle').innerHTML = ruleID == null ? "New Nat Rule" : "Edit Nat Rule";
        //Should perhaps add a loading dialog here
        self.callRemote('getSNATFormData', ruleID).addCallback(function(data) {
            //Should hide the loading dialog here
            self.populateForm('firewallSNATForm', data, ruleID);
            self.showDialogBox("firewallSNATRulesFormDialog", clickElement);
        });
    },

    ///End of SNAT / Source NAT 

    ///Zones

    function initZoneListEvents(self) {
        self.initListEvents("firewallZones", "delZone", function(clickElement, ruleID) {self.prepareZoneForm(clickElement, ruleID);}, "zoneRule");
    },
    
    function initFirewallZoneForm(self) {
        self.attachDialogEvents('firewallZoneFormDialog', false);
        $('fwAddZoneButton').addEvent('click', function(e) {
            self.prepareZoneForm($('fwAddZoneButton'), null);
        });
        //Define the validation information for the form
        zoneFormValidators = new Hash();
        zoneFormValidators["zone"] = function(value) {
            ruleIDEl = $('firewallZoneForm-ruleID');
            res = self.callRemote("checkZoneName", value, ruleIDEl.value);
        }
        //Initialise the form events and the validation handeling
        self.hookForm(  'firewallZoneForm', 
                        'submitZone', 
                        zoneFormValidators,
                        "firewallZoneFormDialog");
        self.initZoneListEvents();

    },
    
    function prepareZoneForm(self, clickElement, ruleID) {
        $('firewallZoneFormTitle').innerHTML = ruleID == null ? "New Zone" : "Edit Zone";
        //Should perhaps add a loading dialog here
        self.callRemote('getZoneFormData', ruleID).addCallback(function(data) {
            //Should hide the loading dialog here
            self.populateForm('firewallZoneForm', data, ruleID);
            self.showDialogBox("firewallZoneFormDialog", clickElement);
        });
    },
    
    function prepareZoneMemberForm(self, clickElement, ruleID) {
        //Do Something
    },

    ///End of Zones

    //Firewall Policy checkboxes
    function initFirewallPolicyForm(self) {
        var blockp2p = $('firewallPolicyForm-blockp2p');
        if(blockp2p) {
            blockp2p.addEvent("click", function(e) {
                self.callRemote('setBlockP2P', blockp2p.checked);
            });
        }
        var blockAll = $('firewallPolicyForm-blockAll');
        blockAll.addEvent("click", function(e) {
            self.callRemote('setBlockAllLAN', blockAll.checked);
        });
        var transProxy = $('firewallPolicyForm-transProxy');
        transProxy.addEvent("click", function(e) {
            self.callRemote('setTransProxy', transProxy.checked);
        });
    },

    ///Firewall QOS
    
    function initQosListEvents(self) {
        self.initListEvents("firewallQosRules", "delQosRule", function(clickElement, ruleID) {self.prepareQosForm(clickElement, ruleID);}, "qosRule");
    },
    
    function initFirewallQosForm(self) {
        self.attachDialogEvents('firewallQosRulesFormDialog', false);
        $('fwAddQosRuleButton').addEvent('click', function(e) {
            self.prepareQosForm($('fwAddQosRuleButton'), null);
        });
        //Define the validation information for the form
        qosFormValidators = new Hash();
        qosFormValidators["port"] = self.validatePort;
        //Initialise the form events and the validation handeling
        self.hookForm(  'firewallQosForm', 
                        'submitQosRule', 
                        qosFormValidators,
                        "firewallQosRulesFormDialog");
        self.initQosListEvents();

    },
    
    function prepareQosForm(self, clickElement, ruleID) {
        $('firewallQosRulesFormTitle').innerHTML = ruleID == null ? "New Qos Rule" : "Edit Qos Rule";
        //Should perhaps add a loading dialog here
        self.callRemote('getQosFormData', ruleID).addCallback(function(data) {
            //Should hide the loading dialog here
            self.populateForm('firewallQosForm', data, ruleID);
            self.showDialogBox("firewallQosRulesFormDialog", clickElement);
        });
    },


    ///End of QOS

    function removeListEntry(self, rid) {
        $(rid).dispose();
    },

    /***
     * Raises a user message
     */
    function setMessage(self, messageHTML, messageID, className, timeOut) {
        var inMessageID = messageID;
        messageID = "errorMessage_"+messageID;
        var mess = $(messageID);
        if(mess) {
            if(mess["timeOut"]) {
                $clear(mess["timeOut"]);
            }
        }
        if(mess == null) {
            mess = new Element('div', {
                'id': messageID,
                'class': className,
                'html': messageHTML,
                'display': 'none'

            });
            $('messageBox').adopt(mess);
            mess['sliderIn'] = new Fx.Slide(mess,{
                duration:300,
            }).hide().slideIn();
        } else {
            //mess['slider'].slideOut().hide().slideIn();
            mess['sliderOut'] = new Fx.Slide(mess,{
                duration:300,
                onComplete: function() {
                    mess.set('class', className);
                    mess.innerHTML = messageHTML;
                    mess['sliderIn'].hide().slideIn();
                }
            }).slideOut();

            //mess['slider'].slideIn();
        }
        if(timeOut > 0) {
            mess["timeOut"] = (function() {
                mess["timeOut"] = null; //Clear the function
                self.clearMessage(inMessageID);
            }).delay(timeOut, mess);
        }
    },

    function clearMessage(self, messageID) {
        messageID = "errorMessage_"+messageID;
        mess = $(messageID);
        if(mess) {
            if(mess["timeOut"]) {
                $clear(mess["timeOut"]);
            }
            //self.cleanupSlide(mess['slide']);
            var slide = new Fx.Slide(mess,{
                duration:300,
                onComplete: function() {
                    self.cleanupSlide(slide);
                    mess.dispose();
                }
            }).slideOut();
        }
    },

    function cleanupSlide(self, slideElement) {
        slideElement.wrapper.dispose();
        slideElement = null;
    },
    /**
     * Facilitates when a form is submitted it then sends the data to the action hook for that form
     * If it gets an ok state then it will hide and clear the form
     * If it gets an error state it then processes a list of field names with their errors marking what problems are in
     * each field
     */
    function hookForm(self, formName, remoteCallName, formValidator, dialogBoxName) {
        //Hook the submit event to the form
        $(formName).addEvent('submit', function(e) {
            new Event(e).stop(); //Stop the usual form processing
            var data = new Hash();
            var form = $(formName);
            for(k in form.elements) {
                if(form.elements[k].type) {
                    if(form.elements[k].type == "checkbox") {
                        data[form.elements[k].name] = form.elements[k].checked;
                    } else {
                        data[form.elements[k].name] = form.elements[k].value;
                    }
                }
            }
            if(self.validateForm(formName, formValidator)){
                self.callRemote(remoteCallName, data).addCallback(function(res) {
                });
                self.hideDialogBox(dialogBoxName);
                self.clearFormErrors(formName);
            }
        });
        if($(formName)['cancel']) {
            $(formName)['cancel'].addEvent('click', function(e) {
                new Event(e).stop(); //Stop the usual form processing
                self.hideDialogBox(dialogBoxName);
                self.clearFormErrors(formName);
            });
        }

    },

    /***
     * Validate a form with provided field and form validation
     * Use vulani formcss and labeling methods to indicate the errors
     */
    function validateForm(self, formName, validator) {
        self.clearFormErrors(formName);
        var out_result = true;
        $$('#'+formName+' div').each(function(element) {
            if(element.hasClass('field')) {
                var fieldName = element.id.split('-')[1]
                var fieldID = formName+"-"+fieldName;
                if(element.type == "checkbox") {
                    var value = $(fieldID).checked;
                } else {
                    var value = $(fieldID).get('value');
                }
                var res = [true,''];
                if(element.hasClass('required')) {
                    res = self.validateRequired(value);
                }
                if(res[0]) {
                    if(validator && value) {
                        //Validator should run the validation for the selected field
                        if(value.length > 0 && validator[fieldName]) {
                            res = validator[fieldName](value);
                        }
                    }
                }
                //Check the result from the validator and then depending on that result
                // Show the messages that the user must see
                if(res) {
                    if(!res[0]) {
                        if(!element.hasClass('error')) {
                            element.addClass('error');
                            var myMessage = new Element('div', {
                                'class': 'message',
                                'html': res[1]
                            });
                            element.adopt(myMessage);
                        }
                    } else {
                        if(res[0] && element.hasClass('error')) {
                            element.removeClass('error');
                        }
                    }
                    out_result &= res[0];
                }
            }
        });
        return(out_result);
    },

    /***
     * Repopulates Zones in provided element
     */
    function resetFieldZones(self, zoneList, fieldElement) {
        //TODO: needs repopulate the zone list with the provided one
    
    },

    /***
     * For each form we should repopulate the zone entries
     *  Must be run when a zone is added or removed.
     */
    function resetAllFieldZones(self, zoneList) {
        var fields = new Array();
        fields[0] = $('firewallRulesForm').elements['dzone'];
        fields[1] = $('firewallRulesForm').elements['szone'];
        for(i=0; i<fields.length; i++) {
            self.resetFieldZones(zoneList, fieldElement);
        }
    },


    /***
     * Populates a form from a data hash normally returned from the serverside method
     **/
    function populateForm(self, formName, data, ruleID) {
        //Call with the data to fill the form
        var form = $(formName);
        for(k in form.elements) {
            if(form.elements[k].type) {
                if(data[form.elements[k].name] != null) {
                    if(form.elements[k].type == "checkbox") {
                        form.elements[k].checked = data[form.elements[k].name];
                    } else {
                        form.elements[k].value = data[form.elements[k].name];
                    }
                    //Fire events like keyup and onBlur
                    form.elements[k].fireEvent('keyup');
                    form.elements[k].fireEvent('blur');
                }
                if(form.elements[k].name == "ruleID") {
                    form.elements[k].value = ruleID;
                }
            }
        }
    },

    /***
     * Inserts a table row (tr) html into a provided listname
     */
    function insertTRHTML(self, listName, ruleID, html, prefix, afterRuleID) {
        //if ruleID is null then we should insert a new html at the end
        if(ruleID) {
            var element = $(ruleID);
        } else {
            var element = new Element('tr', {
                'class': ''
            });
            if(afterRuleID) {
                //if a ruleID has been specified use it to insert after
                $(afterRuleID).inject(element,'after');
            } else {
                $(listName).adopt(element);
            }
        }
        element.innerHTML = html
        self.resetIDS(listName, prefix);
        self.setListAlternateClass(listName);
        if(ruleID) {
            element.addClass("modified"); 
        } else {
            element.addClass("new");
        }
    },

    /***
     * Inserts a list item (li) html into a provided listname
     */
    function insertListHTML(self, listName, ruleID, html, prefix, afterRuleID) {
        //if ruleID is null then we should insert a new html at the end
        if(ruleID) {
            var element = $(ruleID);
        } else {
            var element = new Element('li', {
                'class': ''
            });
            if(afterRuleID) {
                //if a ruleID has been specified use it to insert after
                $(afterRuleID).inject(element,'after');
            } else {
                $(listName).adopt(element);
            }
        }
        element.innerHTML = html
        self.resetIDS(listName, prefix);
        self.setListAlternateClass(listName);
        if(ruleID) {
            element.addClass("modified"); 
        } else {
            element.addClass("new");
        }
    },

    /***
     * Takes a dialog and makes it dragable and resizable
     *  handle is by class hook dialogtopbar (dragable)
     *  handle is by class hook dialogresizer (resizable)
     */
    function attachDialogEvents(self, dialogName, attachResizer) {
        var dialog = $(dialogName);
        $$('#'+dialogName+' div').each(function(element) {
            if(element.hasClass('dialogtopbar')) {
                dialog.makeDraggable({'handle': element});
            }
            if(element.hasClass('dialogresizer')) {
                dialog.makeResizable({'handle': element});
            }
        })
    },

    //Validation Hooks

    function validateRequired(self, value) {
        return([value != null ? value.length > 0 : false, "Required"]);
    },

    function validateIP(self, value) {
        value = value.replace(/^\!/, "")
        return([value.match(/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/) != null, "Invalid IP Address"]);
    },
    
    function validateCIDR(self, value) {
        value = value.replace(/^\!/, "")
        return([value.match(/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,2}$/)!= null, "Invalid CIDR Address"]);
    },

    function validateIPorCIDR(self, value) {
        value = value.replace(/^\!/, "")
        return([value.match(/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/)!= null
            || value.match(/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,2}$/)!= null, 
            "Invalid CIDR or IP Address"]);
    },



    function validatePortRange(self, value) {
        var ranges = value.split(',');
        value.replace(' ','');
        for(i=0; i<ranges.length; i++) {
            if(value.contains(':')) {
                var rng = value.split(':',2);
                if(rng[0] >= rng[1]) {
                    return([false, value + " is invalid second port in portrange is smaller or the same as first"]);
                } else {
                    if(!value.match(/^(6553[0-5]|655[0-2]\d|65[0-4]\d\d|6[0-4]\d{3}|[1-5]\d{4}|[1-9]\d{0,3}|0):(6553[0-5]|655[0-2]\d|65[0-4]\d\d|6[0-4]\d{3}|[1-5]\d{4}|[1-9]\d{0,3}|0)$/)) {
                        return([false, value + " is not a valid port range"]);
                    }
                }
            } else {
                if(!value.match(/^(6553[0-5]|655[0-2]\d|65[0-4]\d\d|6[0-4]\d{3}|[1-5]\d{4}|[1-9]\d{0,3}|0)$/)) {
                    return([false, value + " is not a valid port"]);
                }
            }
        }
        return([true,""]);
    },

    function validatePort(self, value) {
        return([value.match(/^(6553[0-5]|655[0-2]\d|65[0-4]\d\d|6[0-4]\d{3}|[1-5]\d{4}|[1-9]\d{0,3}|0)$/) != null, "Invalid Port"]);
    },
 

    function clearFormErrors(self, formName) {
        $$('#'+formName+' div').each(function(element) {
            if(element.hasClass('error')) {
                element.removeClass('error');
            }
            if(element.hasClass('message')) {
                var old = element.dispose();
            }
        });
    },

    function showDialogBox(self, dialogName, eventElement) {
        $(dialogName).style.left = "400px";
        $(dialogName).style.top = eventElement.offsetTop-150 + "px";
        $(dialogName).style.display = "block"; 
    },

    function hideDialogBox(self, dialogName) {
        $(dialogName).style.display = "none"; 
    },

    function checkSecurity(self) {
        noticeBox = $('securityNotice');
        if(!noticeBox['slider']) {
            noticeBox['slider'] = new Fx.Slide(noticeBox,{
                duration:300,
            }).hide();
            noticeBox.setStyle('display', 'block');
        }

        checkRuleSecurityRes = self.callRemote('checkRuleSecurity');
        checkRuleSecurityRes.addCallback(function(res) {
            if (res.length > 0) {
                noticeBox['slider'].slideIn();
                res.each(function(ruleID) {
                    $(ruleID).addClass('security-error');
                });
            } else {
                noticeBox['slider'].slideOut();
            }
        });
    },

    function attachDelete(self, listName, athenaDelHook, prefix) {
        $$('#'+listName+' td.delete').each(function(el) {
                var deleteFunction = function(e) {
                        new Event(e).stop(); //Stop the usual form processing
                        var parent = el.getParent('li');
                        if(!parent) {
                            var parent = el.getParent('tr');
                        }
                        parent.setStyle('background-color', '#fdeeee');
                        if (!confirm('Are you sure you want to delete this rule?')) {
                            parent.setStyle('background-color', '');
                            self.setListAlternateClass(listName);
                            return
                        }
                        new Fx.Tween(parent,{duration:300}).start('background-color', '#fb6c6c');
                        self.callRemote(athenaDelHook, parent.id);
                        new Fx.Slide(parent,{
                            duration:300,
                            onComplete: function() {
                                parent.dispose();
                                self.setListAlternateClass(listName);
                                if (prefix) {
                                    self.resetIDS(listName, prefix);
                                    //Has to be called here since we rely on the order of the list items
                                }
                            }
                        }).slideOut();
                }
                if(!el["hasDeleteEvent"]) {
                    el.addEvent('click', deleteFunction);
                    el["hasDeleteEvent"] = true;
                }
        });  
    },

    function setListAlternateClass(self, listName) {
        var count = 0;
        $$('#' + listName + ' li').each(function(element) {
            if(element.hasClass('odd')) {
                element.removeClass('odd');
            }
            if(element.hasClass('even')) {
                element.removeClass('even');
            }
            element.addClass(count++ % 2 == 0 ? 'odd' : 'even');
            if(element.hasClass('security-error')) {
                element.removeClass('security-error');
            }
        });
        $$('#' + listName + ' tr').each(function(element) {
            if(element.hasClass('odd')) {
                element.removeClass('odd');
            }
            if(element.hasClass('even')) {
                element.removeClass('even');
            }
            element.addClass(count++ % 2 == 0 ? 'odd' : 'even');
            if(element.hasClass('security-error')) {
                element.removeClass('security-error');
            }
        });
 
        self.checkEmpty(listName);
        self.checkSecurity();
    },

    function resetIDS(self, listName, prefix) {
        var count = 0;
        $$('#' + listName + ' li').each(function(element) {
            element.id = prefix + "_" + count++
        });
        $$('#' + listName + ' tr').each(function(element) {
            element.id = prefix + "_" + count++
        });

    }
    
);
