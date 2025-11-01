import React from 'react';
import { FaUsers, FaCheckCircle } from 'react-icons/fa';

const KnownPersonsLog = ({ persons, compact = false }) => {
  const formatTimestamp = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString();
  };

  if (compact) {
    return (
      <div className="bg-slate-800 rounded-lg shadow-xl overflow-hidden">
        <div className="bg-gradient-to-r from-emerald-600 to-emerald-700 px-4 py-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white flex items-center">
            <FaUsers className="mr-2" />
            Known Persons
          </h2>
          {persons.length > 0 && (
            <span className="bg-white text-emerald-600 text-xs font-bold px-2 py-1 rounded-full">
              {persons.length}
            </span>
          )}
        </div>
        
        <div className="p-4 max-h-80 overflow-y-auto">
          {persons.length === 0 ? (
            <p className="text-gray-400 text-center py-4">No detections yet</p>
          ) : (
            <div className="space-y-2">
              {persons.slice(0, 10).map((person, index) => (
                <div
                  key={index}
                  className="bg-slate-700 rounded-lg p-3 flex items-center justify-between"
                >
                  <div className="flex items-center space-x-3">
                    <FaCheckCircle className="text-green-500" />
                    <div>
                      <p className="text-sm font-semibold text-white">{person.person_name}</p>
                      <p className="text-xs text-gray-400">ID: {person.person_id}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-400">{formatTimestamp(person.timestamp)}</p>
                    <p className="text-xs text-green-400">{(person.similarity * 100).toFixed(0)}%</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-800 rounded-lg shadow-xl overflow-hidden">
      <div className="bg-gradient-to-r from-emerald-600 to-emerald-700 px-6 py-4 flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white flex items-center">
          <FaUsers className="mr-3" />
          Known Persons Log
        </h2>
        {persons.length > 0 && (
          <span className="bg-white text-emerald-600 text-sm font-bold px-3 py-1 rounded-full">
            {persons.length} Detection{persons.length !== 1 ? 's' : ''}
          </span>
        )}
      </div>
      
      <div className="p-6">
        {persons.length === 0 ? (
          <div className="text-center py-12">
            <FaUsers className="text-6xl text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 text-lg">No known persons detected yet</p>
            <p className="text-gray-500 text-sm mt-2">
              Detected known persons will appear here
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {persons.map((person, index) => (
              <div
                key={index}
                className="bg-slate-700 rounded-lg p-4 border-l-4 border-green-500 hover:bg-slate-650 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="bg-green-500 rounded-full p-3">
                      <FaCheckCircle className="text-white text-xl" />
                    </div>
                    <div>
                      <p className="text-lg font-bold text-white">{person.person_name}</p>
                      <p className="text-sm text-gray-400">Person ID: {person.person_id}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-300">{formatTimestamp(person.timestamp)}</p>
                    <div className="mt-2">
                      <span className="bg-green-600 text-white text-xs font-semibold px-3 py-1 rounded-full">
                        Match: {(person.similarity * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default KnownPersonsLog;

