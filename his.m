classdef his
% HIS Handles Hamammatsu Hokawo files
%
% USAGE:
%   var = his; % Will ask for a his file and return the var class object containing its information
%   or
%   var = his('../recording.his'); % Will automatically load 'recording.his' from the parent folder
%
% INPUT:
%   his() - Opens a uigetfile dialog to locate the file
%   his('file.his') - Directly assigns the file 'file.his'
%
% OUTPUT arguments:
%   var - class object containing information about the HIS file
%
% EXAMPLE:
%   var = his('../recording.his');
%
%   Copyright (C) 2016-2018, Javier G. Orlandi <javierorlandi@javierorlandi.com>
%   Standalone version pulled from NETCAL http://www.itsnetcal.com

  properties
    % Handle of the .HIS file
    handle;
    
    % File Identifier (used for fread calls)
    fID;
    
    % Total number of frames
    numFrames;
    
    % Frame widht
    width;
    
    % Frame height
    height;
    
    % Metadata information (from the first frame)
    metadata;
    
    % Full metadata information (for all frames with changes)
    fullMetadata;
    
    % Pixel data type
    pixelType;
    
    % Bits per pixel
    bpp;
    
    % Frame rate
    fps;
    
    % Length of the recording (in s)
    totalTime;
    
    % List containing the position of each frame in the file
    frameOffsetList;
    
    % Size of the metadata contents of each frame
    metadataBytesList;
  end
  methods 
    function obj = his(varargin)
      % First argument might be the file. If not provided, ask for it
      if(nargin >= 1)
        fileName = varargin{1};
      else
        [fileName, pathName, ~] = uigetfile({'*.HIS', 'Hamamatsu HIS files (*.HIS)'}, 'Select file', pwd);
        if(fileName ~= 0)
          fileName = fullfile(pathName, fileName);
        else
          fileName = [];
        end
      end
      % Check for valid file
      if(isempty(fileName))
        ME = MException('HIS:emptyFile', 'No file assigned');
        throw(ME);
      end
      
      % Check for .HIS extension
      [~, ~, fpc] = fileparts(fileName);
      if(~strcmpi(fpc, '.his'))
        ME = MException('HIS:invalidExtension', 'Invalid file extension: %s ',fpc);
        throw(ME);
      end
      % Try to open the file
      obj.fID = fopen(fileName ,'r');
      if(obj.fID == -1)
        ME = MException('HIS:invalidFile', 'Could not open file: %s ',fileName);
        throw(ME);
      end
      obj.handle = fileName;
      
      % Time to preprocess the HIS metadata from the first frame

      % Get the number of frames
      skip = fread(obj.fID, 14); %#ok<NASGU>
      obj.numFrames = fread(obj.fID, 1, 'uint32');

      fseek(obj.fID, 0, 'bof');

      % Read the first batch
      fread(obj.fID, 2, 'uint8=>char');
      comentBytes = fread(obj.fID, 1, 'short');
      obj.width = fread(obj.fID, 1, 'short');
      obj.height = fread(obj.fID, 1, 'short');
      fread(obj.fID, 4);
      dataType = fread(obj.fID, 1, 'short');
      if(dataType == 1)
        obj.pixelType = '*uint8';
        obj.bpp = 8;
      elseif(dataType == 2)
        obj.pixelType = '*uint16';
        obj.bpp = 16;
      else
       obj.pixelType = '*uint16';
       obj.bpp = 16;
      end

      fread(obj.fID, 50);
      metadata_str = fread(obj.fID, comentBytes, 'uint8=>char')';
      metadata_separated = strsplit(metadata_str,';');
      metadata = [];
      for i = 1:length(metadata_separated)
          tmpStr = strsplit(metadata_separated{i},'=');
          if(length(tmpStr) == 2)
              if(isempty(strfind(tmpStr{1},'@')))
                  metadata.(tmpStr{1}) = tmpStr{2};
              end
          end
      end
      
      if(isempty(metadata))
        ME = MException('HIS:emptyMetadata', 'Found empty metadata on: %s', obj.handle);
        throw(ME);
      end
      
      obj.metadata = metadata;
      obj.fps = 1/str2double(obj.metadata.vExpTim1);
      
      % Frame length check
      if(obj.numFrames == 0)
        warning('HIS:noFrames',' Found 0 frames, %s might be corrupt. Trying to recover it', obj.handle);

        obj.numFrames = inf;
        [obj, success] = precacheHISframes(obj, 'mode', 'fast', 'force', true);
        if(~success)
          obj.numFrames = 0;
          warning('HIS:failedRecover','Could not recover %s', obj.handle);
        else
          fprintf('Succesfully recovered %s, %d frames found\n', obj.handle, obj.numFrames);
        end
      end
      obj.totalTime = obj.numFrames/obj.fps;
    
      % We are done with the file (for now)
      fclose(obj.fID);
      obj.fID = [];
      obj = obj.precacheHISframes();
      
    end

    % For convenience
    function obj = openStream(obj)
      obj.fID = fopen(obj.handle);
    end
    
    % For convenience
    function obj = closeStream(obj)
      fclose(obj.handle);
      obj.fID = [];
    end
    
    function obj = precacheHISframes(obj, varargin)
      % PRECACHEHISFRAMES run through the HIS file frame by frame, read the
      % metadata and store the file location of each frame. Needs to be done
      % since metadata size might change from frame to frame
      %
      % USAGE:
      %    precacheHISframes()
      %
      % INPUT optional arguments ('key' followed by its value):
      %    'mode' - 'fast'/'normal'. If fast, it will only process a few frames and try to estimate the position of the ones in between. Normal will process all frames (slow)
      %
      %    frameJump - Positive Integer. Frames to jump on frame position estimation (if mode = 'fast'). frameJump = 1 is equivalent to setting mode = 'normal'
      %
      % EXAMPLE:
      %     curFile = his('file.HIS');
      %     curFile = curFile.precacheHISframes('frameJump', 64);
      %
      % Copyright (C) 2016-2018, Javier G. Orlandi <javierorlandi@javierorlandi.com>
      %
      % See also: his

      params.frameJump = 512;
      params.mode = 'fast'; % 'fast' or 'normal'
      params = parse_pv_pairs(params, varargin);
      
      obj.fID = fopen(obj.handle);
      
      % Get byte offset of each frame since metadata might have variable size
      obj.frameOffsetList = zeros(obj.numFrames, 1);
      obj.metadataBytesList = zeros(obj.numFrames, 1);
      
      % Go to the file origin (just in case)
      fseek(obj.fID, 0, 'bof');

      fprintf('Precaching frames\n');
      
      frameSize = obj.width*obj.height*obj.bpp/8;
      switch params.mode
        % Go frame by frame - read the size of the metadata and move to the next one
        case 'normal'
          for i = 1:obj.numFrames
            fseek(obj.fID, 2, 'cof');
            obj.metadataBytesList(i) = fread(obj.fID, 1, 'short');
            fseek(obj.fID, 60+obj.metadataBytesList(i), 'cof');
            obj.frameOffsetList(i) = ftell(obj.fID);
            fseek(obj.fID, frameSize, 'cof');
            if(eof(obj.fID))
              fprintf('HIS file might be incomplete. Found %d instead of %d valid frames\n', i, obj.numFrames);
              obj.numFrames = i-1;
            end
          end
          % Skip frames and try to predict their correct contents
        case 'fast'
          baseFrameJump = params.frameJump;
          frameJump = baseFrameJump;
          % Start on the first frame
          cFrame = 1;
          % Get metadata size of the first frame
          fseek(obj.fID, 2, 'bof');
          md = fread(obj.fID, 1, 'short');
          obj.metadataBytesList(1) = md;
          obj.frameOffsetList(1) = 64+md;
          totalFrameSize = 64+frameSize+md;
          done = false;
          while(~done)
            nFrame = cFrame + frameJump;
            if(nFrame >= obj.numFrames)
              nFrame = obj.numFrames;
              frameJump = nFrame-cFrame;
            end
            oldmd = md;
            fseek(obj.fID, obj.frameOffsetList(cFrame)+totalFrameSize*(frameJump-1)+frameSize+2, 'bof');
            md = fread(obj.fID, 1, 'short');
            % Check if the file is invalid
            if(frameJump == 1 && md <= 0)
              fprintf('HIS file might be incomplete. Found %d instead of %d valid frames\n', cFrame, obj.numFrames);
              obj.numFrames = cFrame-2;
              obj.totalTime = obj.numFrames/obj.fps;
              obj.metadataBytesList(1:obj.numFrames);
              obj.frameOffsetList(1:obj.numFrames);
              break;
            end
            if(~isnan(oldmd) && md ~= oldmd)
              %fprintf('Inconsistency on frame %d\n', nFrame);
              frameJump = max(1,floor(frameJump/2));
              if(frameJump == 1)
                md = nan;
              else
                md = oldmd;
                continue;
              end
              if(nFrame == obj.numFrames)
                done = true;
              end
            else
              obj.metadataBytesList((cFrame+1):nFrame) = md;
              obj.frameOffsetList((cFrame+1):nFrame) = obj.frameOffsetList(cFrame)+totalFrameSize*((1:frameJump)-1)+frameSize+64+md;
              frameJump = baseFrameJump;
              cFrame = nFrame;
              totalFrameSize = 64+frameSize+md;
              if(nFrame == obj.numFrames)
                done = true;
              end
            end
          end
      end
      metadataInconsistency = find(diff(obj.metadataBytesList) ~= 0);
      if(~isempty(metadataInconsistency))
        frameList = strtrim(sprintf('%d, ', metadataInconsistency(:)+1));
        frameList = frameList(1:end-1);
        fprintf('Changes in HIS metadata size found on frames: %s\n', frameList);
        % Let's store the metadata of these frames
        obj.fullMetadata = cell(length(metadataInconsistency), 1);
        for it1 = 1:length(metadataInconsistency)
          cFrame = metadataInconsistency(it1)+1;
          % Need to read the previou frame, since the offset is the actual frame position
          fseek(obj.fID, obj.frameOffsetList(cFrame-1)+frameSize+2, 'bof');
          md = fread(obj.fID, 1, 'short');
          % Get to the metadata position
          fread(obj.fID, 3, 'short');
          fread(obj.fID, 54);
          metadata_str = fread(obj.fID, md, 'uint8=>char')';
          metadata_separated = strsplit(metadata_str,';');
          metadata = []; %#ok<*PROPLC>
          for i = 1:length(metadata_separated)
              tmpStr = strsplit(metadata_separated{i},'=');
              if(length(tmpStr) == 2)
                  if(isempty(strfind(tmpStr{1},'@')))
                      metadata.(tmpStr{1}) = tmpStr{2};
                  end
              end
          end
          obj.fullMetadata{it1} = metadata;
        end
      end

      % Now let's add a check for corrupted HIS files (missing frames)
      lastInvalidFrame = [];
      for it = obj.numFrames:-1:1
        fseek(obj.fID, obj.frameOffsetList(it), 'bof');
        fread(obj.fID, 1, 'short'); % Read one short to test for feof
        if(~feof(obj.fID))
          break;
        else
          lastInvalidFrame = it;
        end
      end
      if(~isempty(lastInvalidFrame))
        fprintf('HIS file is incomplete. Found %d instead of %d valid frames', it-1, obj.numFrames);
        obj.numFrames = it;
      end
      % Update number of frames and duration (just in case)
      if(~isinf(obj.numFrames))
        obj.totalTime = obj.numFrames/obj.fps;
        obj.metadataBytesList(1:obj.numFrames);
        obj.frameOffsetList(1:obj.numFrames);
      else
        ME = MException('HIS:invalidFrames', 'number of Frames after precaching is Inf. Something went wrong');
        throw(ME);
      end
      
      % We are done
      fclose(obj.fID);
      obj.fID = [];
    end

    function img = getFrame(obj, idx)
      % Return the contents of frame number idx
      if(isempty(obj.fID))
        obj.fID = fopen(obj.handle);
        newOpen = true;
      else
        newOpen = false;
      end
      fseek(obj.fID, obj.frameOffsetList(idx), 'bof');
      img = fread(obj.fID,obj.width*obj.height, obj.pixelType);
      img = reshape(img, [obj.width, obj.height])'; % TRANSPOSE NEEDED
      if(newOpen)
        fclose(obj.fID);
      end
    end
    
    function hFig = previewFrame(obj, idx)
      % Return the contents of frame number idx
      img = obj.getFrame(idx);
      hFig = figure;
      imagesc(img);
      axis equal tight;
      colormap gray;
      colorbar;
      [~, fileName, ~] = fileparts(obj.handle);
      title(sprintf('%s - frame: %d, time: %.2f s', fileName, idx, idx/obj.fps));
    end
  end
  methods (Static)
    function params=parse_pv_pairs(params,pv_pairs)
      % parse_pv_pairs: parses sets of property value pairs, allows defaults
      % usage: params=parse_pv_pairs(default_params,pv_pairs)
      %
      % arguments: (input)
      %  default_params - structure, with one field for every potential
      %             property/value pair. Each field will contain the default
      %             value for that property. If no default is supplied for a
      %             given property, then that field must be empty.
      %
      %  pv_array - cell array of property/value pairs.
      %             Case is ignored when comparing properties to the list
      %             of field names. Also, any unambiguous shortening of a
      %             field/property name is allowed.
      %
      % arguments: (output)
      %  params   - parameter struct that reflects any updated property/value
      %             pairs in the pv_array.
      %
      % Example usage:
      % First, set default values for the parameters. Assume we
      % have four parameters that we wish to use optionally in
      % the function examplefun.
      %
      %  - 'viscosity', which will have a default value of 1
      %  - 'volume', which will default to 1
      %  - 'pie' - which will have default value 3.141592653589793
      %  - 'description' - a text field, left empty by default
      %
      % The first argument to examplefun is one which will always be
      % supplied.
      %
      %   function examplefun(dummyarg1,varargin)
      %   params.Viscosity = 1;
      %   params.Volume = 1;
      %   params.Pie = 3.141592653589793
      %
      %   params.Description = '';
      %   params=parse_pv_pairs(params,varargin);
      %   params
      %
      % Use examplefun, overriding the defaults for 'pie', 'viscosity'
      % and 'description'. The 'volume' parameter is left at its default.
      %
      %   examplefun(rand(10),'vis',10,'pie',3,'Description','Hello world')
      %
      % params = 
      %     Viscosity: 10
      %        Volume: 1
      %           Pie: 3
      %   Description: 'Hello world'
      %
      % Note that capitalization was ignored, and the property 'viscosity'
      % was truncated as supplied. Also note that the order the pairs were
      % supplied was arbitrary.
      
      % Original file:
      % Copyright (c) 2009, John D'Errico
      % https://www.mathworks.com/matlabcentral/fileexchange/9082-parse_pv_pairs

      npv = length(pv_pairs);
      n = npv/2;

      if n~=floor(n)
        error 'Property/value pairs must come in PAIRS.'
      end
      if n<=0
        % just return the defaults
        return
      end

      if ~isstruct(params)
        error 'No structure for defaults was supplied'
      end

      % there was at least one pv pair. process any supplied
      propnames = fieldnames(params);
      lpropnames = lower(propnames);
      for i=1:n
        p_i = lower(pv_pairs{2*i-1});
        v_i = pv_pairs{2*i};

        ind = strcmp(p_i,lpropnames);
        if isempty(ind)
          ind = find(strncmp(p_i,lpropnames,length(p_i)));
          if isempty(ind)
            error(['No matching property found for: ',pv_pairs{2*i-1}])
          elseif length(ind)>1
            error(['Ambiguous property name: ',pv_pairs{2*i-1}])
          end
        end
        p_i = propnames{ind};

        % override the corresponding default in params
        %params = setfield(params,p_i,v_i);
        params.(p_i) = v_i;
      end
    end
  end
end
