/*!
 * admit.js 
 * http://admit.astro.umd.edu
 */
var admit = (function (admit) {

/**
 * Gets the browser name or returns an empty string if unknown. 
 * This function also caches the result to provide for any 
 * future calls this function has.
 * http://stackoverflow.com/questions/9847580/how-to-detect-safari-chrome-ie-firefox-and-opera-browser
 * @returns {string}
 */
admit.browser = function() {
    // Return cached result if available, else get result then cache it.
    if (admit.browser.prototype._cachedResult)
        return admit.browser.prototype._cachedResult;

    var isOpera = !!window.opera || navigator.userAgent.indexOf(' OPR/') >= 0;
    // Opera 8.0+ (UA detection to detect Blink/v8-powered Opera)
    var isFirefox = typeof InstallTrigger !== 'undefined';// Firefox 1.0+
    var isSafari = Object.prototype.toString.call(window.HTMLElement).indexOf('Constructor') > 0;
    // At least Safari 3+: "[object HTMLElementConstructor]"
    var isChrome = !!window.chrome && !isOpera;// Chrome 1+
    var isIE = /*@cc_on!@*/false || !!document.documentMode; // At least IE6

    return (admit.browser.prototype._cachedResult =
        isOpera ? 'Opera' :
        isFirefox ? 'Firefox' :
        isSafari ? 'Safari' :
        isChrome ? 'Chrome' :
        isIE ? 'IE' :
        'Unknown');
};

/* Generate a uniqueid string for browser storage key
 * See http://stackoverflow.com/questions/105034/create-guid-uuid-in-javascript
 */
admit.uniqueid = function(){
    var d = new Date().getTime();
    if(window.performance && typeof window.performance.now === "function"){
        d += performance.now(); //use high-precision timer if available
    }
    var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = (d + Math.random()*16)%16 | 0;
        d = Math.floor(d/16);
        return (c=='x' ? r : (r&0x3|0x8)).toString(16);
    });
    return uuid;
}

/** 
 * Set and get cookies.
 * http://www.w3schools.com/js/js_cookies.asp
 */
admit.setCookie = function(cname, cvalue, exdays) {
    var d = new Date();
    d.setTime(d.getTime() + (exdays*24*60*60*1000));
    var expires = "expires="+ d.toUTCString();
    document.cookie = cname + "=" + cvalue + "; " + expires;
}

admit.getCookie=function(cname) {
    var name = cname + "=";
    var ca = document.cookie.split(';');
    for(var i = 0; i <ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length,c.length);
        }
    }
    return "";
}

//*****************************************************************************
// A knockout type to present data in the table with a given
// precision, but not lose precision in the underlying data.
// See http://jsfiddle.net/9jFUa/2/
//*****************************************************************************

    ko.formattedObservable = function(initalValue, precision) {
        //private variables
        var _backingField = ko.observable(initalValue);

        var result = ko.computed({
            read: function() {
                return _backingField().toFixed(precision);
            },
            write: function(newValue) {
                var parsed = parseFloat(newValue);
                _backingField(isNaN(parsed) ? newValue: parsed);
                _backingField.valueHasMutated();
            }
        });

        result.val = _backingField;
            
        return result;
    };

//*****************************************************************************
// A knockout extender to keep only a certain level of precision.
// Take from knockout example: 
// http://knockoutjs.com/documentation/extenders.html
// See also http://stackoverflow.com/questions/7704268/formatting-rules-for-numbers-in-knockoutjs
//*****************************************************************************

    ko.extenders.numeric = function(target, precision) {
        //create a writable computed observable to intercept writes to our observable
        var result = ko.pureComputed({
            read: target,  //always return the original observables value
            write: function(newValue) {
                var current = target(),
                    roundingMultiplier = Math.pow(10, precision),
                    newValueAsNum = isNaN(newValue) ? 0 : parseFloat(+newValue),
                    valueToWrite = Math.round(newValueAsNum * roundingMultiplier) / roundingMultiplier;
                //console.log("computedWrite: "+current); 
                //only write if it changed
                if (valueToWrite !== current) {
                    target(valueToWrite);
                } else {
                    //if the rounded value is the same, but a different value was written, force a notification for the current field
                    if (newValue !== current) {
                        target.notifySubscribers(valueToWrite);
                    }
                }
            }
        }).extend({ notify: 'always' });

     
        //initialize with current value to make sure it is rounded appropriately
        result(target());
     
        //return the new computed observable
        return result;
    };

ko.extenders.sessionStore = function(target, key) {
        var value = amplify.store.sessionStorage(key) || target(); 
        //console.log("local store " + key + "=" +target() );

        var result = ko.computed({
            read: target,
            write: function(newValue) {
                amplify.store.sessionStorage(key, newValue);
                target(newValue);
            }
        });

        result(value);

        return result;
    };

//*********************************************
// Represents a single line list row.
//*********************************************
/* We keep full precision on intensity, offset, fwhm, velocity 
 * energies down to milliK are good enough 
 * channels only need integer precision 
 */

    admit.LineIDTableRow = function(line, groupID) {
        var self = this;
        self.frequency     = ko.observable(line.frequency);
        var storagekey     = admit.uniqueid();
        self.uid           = ko.observable(line.uid).extend({sessionStore:'uid'+storagekey});
        self.formula       = ko.observable(line.formula).extend({sessionStore:'formula'+storagekey});
        self.name          = ko.observable(line.name).extend({sessionStore:'name'+storagekey});
        self.transition    = ko.observable(line.transition).extend({sessionStore:'transition'+storagekey});
        self.velocity      = ko.formattedObservable(Number(line.velocity),4).extend({sessionStore:'velocity'+storagekey});
        self.velo= ko.formattedObservable(Number(line.velocity),4);
        self.velocity      = self.velo.extend({sessionStore:'velocity'+storagekey});
        // grmph. because a json write is a ko read [i.e. same as html display], we only get lower 
        // precision value when sending back to server. Therefore, keep a pureComputed value that
        // tracks the data value so full precision is kept.  Only need this for
        // velocities and intensity.
        self.velocity_raw  = ko.pureComputed(function(){return self.velo.val();},self);
        self.elower        = ko.observable(Number(line.El)).extend({numeric: 3});
        self.eupper        = ko.observable(Number(line.Eu)).extend({numeric: 3});
        self.linestrength  = ko.observable(Number(line.linestrength)).extend({numeric: 4});
        self.peakintensity = ko.formattedObservable(Number(line.peakintensity),4);
        self.peakintensity_raw = ko.pureComputed(function(){return self.peakintensity.val();},self);
        self.peakoffset    = ko.formattedObservable(Number(line.peakoffset),4);
        self.peakoffset_raw = ko.pureComputed(function(){return self.peakoffset.val();},self);
        self.fwhm          = ko.formattedObservable(Number(line.fwhm),4);
        self.fwhm_raw      = ko.pureComputed(function(){return self.fwhm.val();},self);
        self.startchan     = ko.observable(Number(line.startchan)).extend({numeric: 0, sessionStore:'startchan'+storagekey});
        self.endchan       = ko.observable(Number(line.endchan)).extend({numeric: 0, sessionStore:'endchan'+storagekey});
        self.peakrms         = ko.observable(Number(line.peakrms)).extend({numeric: 1});
        self.blend         = ko.observable(Number(line.blend)).extend({numeric: 0});
        self.force        = ko.observable(line.force);

        if (self.force == "True") { //sigh, string not bool.
            self.disposition   = ko.observable("force").extend({sessionStore:'disposition'+storagekey});
        } else {
            self.disposition   = ko.observable("accept").extend({sessionStore:'disposition'+storagekey});
        }
        // we need unique radio button group name for each row..
        self.buttonGroup   = ko.observable("buttonGroup"+groupID);
        self.isForced   = function() {return self.disposition() == 'force';}
        self.isRejected = function() {return self.disposition() == 'reject';}
        //console.log(self.uid()+" "+self.disposition()+ " force=" + self.force() + " reject=" +self.isRejected())

    };

//*********************************************
// The view model for the line list editor
//*********************************************
    admit.LineIDTableViewModel = function() {
        var self = this;
        //self.uuid = -1;
        self.taskid = -1;
        self.naxis3 = -1;
        self.rowcounter=0;
        self.lineIDTableHeader = ko.observableArray([]);
        self.rows = ko.observableArray([]);

        //***************************************
        // Initialization after construction
        //***************************************
        self.initialize = function(data) {
            //stored_data = amplify.store( self.uuid );
            //console.log("store val : " +stored_data);
            //if (stored_data) {
            //    console.log("found stored data with uuid " + self.uuid);
            //    self.setheader(stored_data.columns,stored_data.units);
            //    self.update(stored_data);
                //self.origdata = stored_data;
            //} else {
             //   console.log("no stored data for uuid " +self.uuid+ ". Using inputs");
                self.taskid = data.taskid
                self.naxis3 = data.naxis3
                var table   = data.linetable
                self.setheader(table.columns,table.units);
                self.update(table);
                self.origdata = table;
              //  if (self.uuid != -1) {
               //    console.log("storing data with uuid " + self.uuid);
                   //amplify.store(self.uuid,data);
                //   check = amplify.store(self.uuid);
                 //  console.log("check val : " +check);
               // } else {
                   //console.log("not storing data because uuid = " + self.uuid);
               // }
            //}
        }

        //ugh. Want to hide the non-editable columns in the table editor
        self.hiddencols = [ "El",
                            "Eu",
                            "linestrength",
                            "peakintensity",
                            "peakoffset",
                            "fwhm", 
                            "peakrms",
                            "force"];
        self.visible = ko.observableArray([true,true,true]);
        self.origvisible = ko.observableArray([true,true,true]);

        //*********************************************
        // Set the table header.
        // @param columns - array of column names 
        // @param units   - array of units
        //*********************************************
        self.setheader = function(columns,units) {
            self.lineIDTableHeader.push({name:"accept",unit:"", xhidden:false});
            self.lineIDTableHeader.push({name:"force",unit:"", xhidden:false});
            self.lineIDTableHeader.push({name:"reject",unit:"", xhidden:false});
            for ( i = 0; i < columns.length; i++) {
                   var index = self.hiddencols.indexOf(columns[i]);
                   var hideme = (index == -1) ? false : true ;
                   self.visible.push(!hideme);
                   self.origvisible.push(!hideme);
                   self.lineIDTableHeader.push({name:columns[i], unit:"["+units[i]+"]", xhidden: hideme});
            }
        }

        //* For the lineID table on the main index.html, we don't want the 
        //* Accept, Force, Reject radio buttons, so delete them.  
        //* They are the first three entries in lineIDTableHeader so shift()
        //* will remove them.
        self.delAFR = function() {
            for (i = 0; i < 3; i++){
                self.lineIDTableHeader.shift();
            }
        }

        //*********************************************
        // Update data from a JSON object
        //*********************************************
        self.update = function(data) {
            self.rowcounter=0;
            //console.log(self);
            //console.log(data);
            //console.log("numrows = " + self.rows().length + "numdata = " + data.lines.length);
            if (self.rows().length > 0) {self.rows.removeAll();}
            // have to push new rather than just change the values or
            // the view does not get updated. See 
            // http://knockoutjs.com/documentation/observableArrays.html
            // http://www.knockmeout.net/2012/04/knockoutjs-performance-gotcha.html
            for ( i = 0; i < data.lines.length; i++ ) {
              //console.log(data.lines[i]);
              self.rowcounter++;
              self.rows.push(new admit.LineIDTableRow(data.lines[i],self.rowcounter));
            }
            //for ( i=0;i<self.visible().length;i++){
            //  console.log("self.visible["+i+"]="+self.visible()[i]);
            //}
        }

        //*********************************************
        // Reset the data to the original from the server
        //*********************************************
        self.reset = function() {
              //console.log("reset calling getJSON ");
              //$.getJSON("lltable.json", self.update);
              sessionStorage.clear();
              self.update(self.origdata);
              //amplify.store(self.uuid,self.origdata);
              
        }

        //*********************************************
        /* add a blank line to the table for user to edit */
        //*********************************************
        self.add = function() {
              var emptydata = { 
                    frequency: "", 
                    uid: "", 
                    formula: "", 
                    name: "", 
                    transition: "", 
                    Eu: "", 
                    El: "", 
                    linestrength: "", 
                    blend: "", 
                    endchan: "", 
                    fwhm: "",
                    peakintensity: "", 
                    peakoffset: "", 
                    peakrms: "", 
                    startchan: "", 
                    velocity: ""
             };
             // if you use "var emptyline", it is not mutable!
             self.rowcounter++;
             emptyline = new admit.LineIDTableRow(emptydata,self.rowcounter);
             emptyline.disposition("reject");
             self.rows.push(emptyline);
        }

        //*********************************************
        /* set force and reject keys for LineID_AT */
        //*********************************************
        self.setforcereject= function() {
              elemid = "#admitform-"+self.taskid.toString();
              console.log("set lineid string for %s",elemid);
              var aform = $(elemid);
              //console.log("aform is ",aform);
              // Build up the payload to send to the server
              // command name
              var payload = aform.serializeJSON();
              payload.command = "forcereject";
              // ADMIT task ID (should be a lineid task!)
              payload.taskid = self.taskid;
              // add uuid to tell server we cached this locally
              //payload.uuid = self.uuid;
              // add linelist table rows
              payload.rows = ko.toJS(self.rows());
              sessionStorage.buttonState = "lalalala"

              // convert to JSON format for send.
              var jsonpayload = JSON.stringify(payload);

              // do the post
              $.post(
                 aform.attr("action"),
                 jsonpayload,
                 self.responseMethod
              );
              return false;

        }

        //*********************************************
        /* overwrite the linelength BDP based on user's edits */
        //*********************************************
        self.writebdp= function() {
          var aform = $(document.admitform);
          // Build up the payload to send to the server
          // command name
          var payload = aform.serializeJSON();
          // ADMIT task ID (should be a lineid task!)
          payload.command = "linelistbdp";
          payload.taskid = self.taskid;
          // add linelist table rows
          payload.rows = ko.toJS(self.rows());

          /*console.log("payload.taskid = "+payload.taskid);
          console.log("self.taskid = "+self.taskid);
          console.log("row[0].peakoffset= "+self.rows()[0].peakoffset());
          console.log("row[0].peakoffset.raw= "+self.rows()[0].peakoffset.val());
          console.log("row[0].velocity = "+self.rows()[0].velocity());
          console.log("row[0].velocity.raw= "+self.rows()[0].velocity.val());
          */

          // convert to JSON format for send.
          var jsonpayload = JSON.stringify(payload);

          // debug
          console.log("json payload="+jsonpayload);
          //document.getElementById('result').innerHTML = jsonpayload;

          // don't let them click twice.
          var run_button = document.getElementById('writebdpbutton');
          run_button.disabled=true;

          // do the post
          $.post(
             aform.attr("action"),
             jsonpayload,
             self.responseMethod
          );

        }

        //*********************************************
        // Function to call when server returns with a response
        //*********************************************
        self.responseMethod = function(response_code) {
           //document.getElementById('response').innerHTML = response_code;
           // re-enable the button
           var run_button = document.getElementById('writebdpbutton');
           run_button.disabled=false;
        }

        //*********************************************
        // We must validate the user inputs at some point
        //*********************************************
        self.validate = function() {
              //@todo use ko.validate library?
              console.log("check forced lines for overlapping channels or repeated entries");
              alert("If you had bad inputs, I would tell you here.");
              return true;
        }

        self.showhidden = true;

        /* currently unused. a pain in the butt */
        self.togglehidden= function() {
             console.log("togglehidden");
             self.showhidden=!self.showhidden;
              
        }

        //self.resetRow = function() { }

    };


  return admit;
}(admit || {}));
